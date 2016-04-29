# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Models Utils
"""
import inspect
from weakref import WeakKeyDictionary

# Exceptions ##################################################################


class WrongStateException(RuntimeError):
    """
    Raised when a method/action is attempted but the object's current state
    does not support that method.
    """
    pass


class SteadyStateException(WrongStateException):
    """
    Raised when attempting to wait until object reaches a state that fulfills a certain condition
    but the object's current state is steady, i.e., it is not expected to change.
    """
    pass


# Functions ###################################################################

def format_help_text(help_text):
    """
    Fix whitespace in a multi-line help_text string for a django field.

    Removes new lines and repeated whitespace
    """
    return " ".join(help_text.replace('\n', ' ').split())


# Classes #####################################################################

class ValidateModelMixin(object):
    """
    Make :meth:`save` call :meth:`full_clean`.

    .. warning:
        This should be the left-most mixin/super-class of a model.

    More info:

    * "Why doesn't django's model.save() call full clean?"
        http://stackoverflow.com/questions/4441539/
    * "Model docs imply that ModelForm will call Model.full_clean(),
        but it won't."
        https://code.djangoproject.com/ticket/13100

    https://gist.github.com/glarrain/5448253
    """
    def save(self, *args, **kwargs):
        """Call :meth:`full_clean` before saving."""
        self.full_clean()
        super(ValidateModelMixin, self).save(*args, **kwargs)

    def set_field_defaults(self):
        """
        Set default values.

        We don't use django field 'defaults=callable' because changes to the field defaults
        affect automatically generated migrations, generating a new one when settings don't match

        This method is called by clean_fields() before validation and save()
        """
        pass

    def clean_fields(self, exclude=None):
        """
        Set default values before validation.
        """
        if not self.pk:
            self.set_field_defaults()
        super().clean_fields(exclude=exclude)


class ClassProperty(property):
    """ Same as built-in 'property' global but also works when accessed as a class attribute """
    def __get__(self, cls, owner):
        # TODO: Requires astroid 2.0+ to pass pylint
        # https://bitbucket.org/logilab/pylint/issues/439/confused-by-descriptors
        return self.fget.__get__(None, owner)()  # pylint: disable=no-member


class ResourceState:
    """
    A [finite state machine] state class representing the overall state of a resource,
    such as a server, a database, a DNS entry, etc.
    """
    # state_id: A string uniquely identifying this state
    state_id = None

    @ClassProperty
    @classmethod
    def name(cls):
        """
        name: Human-readable name of this state, suitable for display as "Status: _______"

        Doesn't need to be a property; override in the subclass using just 'name = "Name"'
        """
        return cls.__name__

    @ClassProperty
    @classmethod
    def description(cls):
        """
        description: Human-readable explanation of this state (1-2 sentences)

        Defaults to the state class's docstring, but you can override it.
        Doesn't need to be a property; override in the subclass using just 'description = "..."'
        """
        return inspect.getdoc(cls).strip()

    def __str__(self):
        return "{} [{}]".format(self.name, self.state_id)

    def __eq__(self, obj):
        """
        Syntactic sugar to make comparing states easier.

        obj should be a ResourceState class or instance.

        Returns true if the class/instance is of the exact same state class.
        To compare with inherited classes etc., use a full isinstance or issubclass expression.
        """
        if inspect.isclass(obj):
            return type(self) is obj  # pylint: disable=unidiomatic-typecheck
        else:
            return type(self) is type(obj)

    def __hash__(self):
        """ Get an appropriate hash value (for consistency with __eq__) """
        return hash(type(self))

    @classmethod
    def one_of(cls, *state_classes):
        """ Syntactic sugar to make comparing an instance to a set of types easier """
        return issubclass(cls, state_classes)

    def __init__(self, resource, state_manager):
        """
        Instantiate this state
        """

    class Enum:
        """
        Syntacic sugar for declaring a group of ResourceState classes inside a class.

        Use like:

        class MyStates(ResourceState.Enum):
            class State1(ResourceState):
                state_id = '1'
            class State2(ResourceState):
                state_id = '2'

        or if states are already declared, use like:
        class MyStates(ResourceState.Enum):
            State1, State2 = State1, State2

        Then you can use MyStates.states to get a list of the state classes.
        """
        @ClassProperty
        @classmethod
        def states(cls):
            """
            Get a tuple listing all the classes defined within this class
            """
            def generate():
                """ Search for ResourceStates defined on this class or inherited classes """
                for name in dir(cls):
                    if name[:1] == '_' or name == 'states':
                        continue
                    state = getattr(cls, name)
                    if inspect.isclass(state) and issubclass(state, ResourceState):
                        yield state
            return tuple(generate())


class ResourceStateDescriptor:
    """
    Descriptor which implements a finite state machine.

    Assign an instance of this to a class attribute such as 'state'. This will create a 'state'
    property that always returns an instance of one of the allowed state_classes.
    The 'state' property cannot be assigned to; only the current state instance is allowed to
    change the state. This makes it easy to reason about the behavior of the state.
    """
    def __init__(self, state_classes, default_state):
        """
        Instantiate a ResourceStateDescriptor to manage a state machine.

        state_classes: A list of class types that are valid states for this state machine.
        default_state: If no state has been set, assume the state is this state class.
        """
        self.state_classes = frozenset(state_classes)
        assert all(isinstance(state_class.state_id, str) for state_class in state_classes), \
            "A resource's states must each declare a state_id string"
        assert len(set(state_class.state_id for state_class in state_classes)) == len(state_classes), \
            "A resource's states must each have a unique state_id"
        assert default_state in state_classes
        self.default_state_class = default_state
        self.state_id_map = {state_class.state_id: state_class for state_class in self.state_classes}
        self.cache = WeakKeyDictionary()  # This holds the current state instance for each resource

    # Public API (implements the python descriptor interface)

    def __get__(self, resource, _type=None):
        """
        Get the current state
        """
        if resource is None:
            return self  # when accessed via the class, return this descriptor itself.
        try:
            state = self.cache[resource]
        except KeyError:
            # 'resource' refers to a brand new object, whose state property hasn't been accessed
            # yet. Load the state from the django field, or use the default state.
            state = self._set_state(resource, self._get_initial_state(resource))
        assert type(state) in self.state_classes  # pylint: disable=unidiomatic-typecheck
        return state

    def __set__(self, resource, value):
        """
        Prevent changes to the state other than through the allowed transitions
        """
        raise AttributeError("You cannot assign to a state machine attribute to change the state.")

    def only_for(self, *accepted_states):  # Not sure why this warning is raised: pylint: disable=no-self-use
        """
        Decorator that can annotate a method and will raise an error if the method is called
        when the state machine is not in one of the specified states (accepted_states).

        If applied to a method, that method will get a new '.is_available()' attribute that can
        be used to determine if the method can be called or not (is in an appropriate state or
        not).

        If applied to a property, it works similarly to a method, but the '.is_available()'
        feature is not present.
        """
        for state in accepted_states:
            assert state in self.state_classes

        def wrap(method):
            """
            Create a MagicWrapper descriptor that will implement the only_for() behavior.
            """
            def require_valid_state(resource):
                """
                Raise a WrongStateException if resource is not in one of the required states
                """
                state = self.__get__(resource)
                if not isinstance(state, accepted_states):
                    #TODO: why is no-member disabled?
                    raise WrongStateException("The method '{}' cannot be called in this state ({} / {}).".format(
                        method.__name__, state.name, state.__class__.__name__  # pylint: disable=no-member
                    ))

            descriptor = self

            class MagicWrapper:
                """ Class which can wrap a method; the result can be used as a property or as a method. """
                def __call__(self, resource):
                    """ We are wrapping a property, not a method. No fancy stuff needed. """
                    require_valid_state(resource)
                    return method(resource)

                def __get__(self, resource, _type):
                    """ Get the (wrapped) method, and add a .is_available method to it """
                    def wrapped_method(*args, **kwargs):
                        """ Wrapper around the method which checks the state requirements first """
                        require_valid_state(resource)
                        return method(resource, *args, **kwargs)
                    wrapped_method.is_available = lambda: isinstance(descriptor.__get__(resource), accepted_states)
                    return wrapped_method

            return MagicWrapper()
        return wrap

    def transition(self, to_state, from_states=None):
        """
        Returns a "transition" method, which can be called to change the current state from
        state(s) 'from' to 'to'.

        from_states can be a state class, a tuple of classes, a parent class or mixin of various
        state classes, a tuple of mixins, etc.. if None, any valid state will be accepted.
        """
        assert to_state in self.state_classes
        if from_states is None:
            from_states = tuple(self.state_classes)

        def do_transition(resource):
            """ The method that performs a specific transition """
            current_state = self.__get__(resource)
            if from_states and not isinstance(current_state, from_states):
                #TODO: why is no-member disabled?
                raise WrongStateException("This transition cannot be used to move from {} to {}".format(
                    current_state.name, to_state.name  # pylint: disable=no-member
                ))
            self._set_state(resource, to_state)
        do_transition.from_states = from_states  # Convenient way for other code to inspect this transition
        do_transition.to_state = to_state  # Convenient way for other code to inspect this transition
        return do_transition

    # Internal helper methods:

    def _get_initial_state(self, resource):
        """
        Get the initial ResourceState subclass that should be used for this resource.
        """
        assert resource not in self.cache, "_get_initial_state is only for determining the initial state."
        return self.default_state_class

    def _get_state_class_from_id(self, state_id):
        """
        Given a state_id, get the ResourceState subclass, or None
        """
        return self.state_id_map.get(state_id)

    def _set_state(self, resource, new_state_class):
        """
        Internal method: Set the state of resource to new_state_class

        new_state_class should be a ResourceState subclass (not instantiated).
        """
        assert new_state_class in self.state_classes
        new_state = new_state_class(resource=resource, state_manager=self)
        self.cache[resource] = new_state
        return new_state


class ModelResourceStateDescriptor(ResourceStateDescriptor):
    """
    Descriptor which implements a finite state machine, backed by a django field.
    """
    def __init__(self, state_classes, default_state, model_field_name):
        """
        Instantiate a ResourceStateDescriptor to manage a state machine.

        state_classes: A list of class types that are valid states for this state machine.
        default_state: If no state has been set, assume the state is this state class.
        model_field_name: The name of a django CharField to keep updated with the name of the
            current state.
        """
        super().__init__(state_classes, default_state)
        self.cache = None  # A django field is used as the storage of the current state.
        self.model_field_name = model_field_name

    # Public API (implements the python descriptor interface)

    def __get__(self, resource, _type=None):
        """
        Get the current state
        """
        if resource is None:
            return self  # when accessed via the class, return this descriptor itself.
        state_class = self._get_state_class_from_id(getattr(resource, self.model_field_name))
        if state_class:
            assert state_class in self.state_classes
            return state_class(resource=resource, state_manager=self)
        else:
            return self._set_state(resource, self.default_state_class)

    @property
    def model_field_choices(self):
        """
        Get a tuple of (state_id, name) pairs.

        Suitable for passing to a django CharField choices parameter.
        """
        return sorted((state.state_id, state.__name__) for state in self.state_classes)

    # Internal helper methods:

    def _set_state(self, resource, new_state_class):
        """
        Internal method: Set the state of resource to new_state_class

        new_state_class should be a ResourceState subclass (not instantiated).
        """
        assert new_state_class in self.state_classes
        new_state = new_state_class(resource=resource, state_manager=self)
        setattr(resource, self.model_field_name, new_state_class.state_id)
        # Save changes to this one field only
        resource.save(update_fields=[self.model_field_name])
        return new_state
