# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
model utils - Tests, mostly for state machine
"""

# Imports #####################################################################

from unittest import TestCase
from mock import Mock

from django.db import models

from instance.models.utils import (
    ResourceState,
    ResourceStateDescriptor,
    ModelResourceStateDescriptor,
    WrongStateException,
)

# Tests #######################################################################


class ResourceStateTests(TestCase):
    """
    Basic tests for the ResourceState class
    """

    def test_state_declarations(self):
        """
        Basic properties of a state can be declared easily and read from an instance or class.
        """
        class Alpha(ResourceState):
            """
            The first letter of the greek alphabet
            """
            state_id = 'alpha'

        alpha = Alpha(resource=Mock(), state_manager=Mock())

        self.assertEqual(Alpha.state_id, 'alpha')
        self.assertEqual(alpha.state_id, 'alpha')
        self.assertEqual(Alpha.name, 'Alpha')
        self.assertEqual(alpha.name, 'Alpha')
        self.assertEqual(alpha.description, "The first letter of the greek alphabet")
        self.assertEqual(Alpha.description, "The first letter of the greek alphabet")

        class Beta(ResourceState):
            """ A state called Beta """
            state_id = 'beta'
            name = 'Beta!'
            description = "The second letter of the greek alphabet"

        beta = Beta(resource=Mock(), state_manager=Mock())

        self.assertEqual(Beta.state_id, 'beta')
        self.assertEqual(beta.state_id, 'beta')
        self.assertEqual(Beta.name, 'Beta!')
        self.assertEqual(beta.name, 'Beta!')
        self.assertEqual(Beta.description, "The second letter of the greek alphabet")
        self.assertEqual(beta.description, "The second letter of the greek alphabet")

        # One last check of another docstring format (make sure it has no trailing space):

        class Gamma(ResourceState):
            """ The third letter of the greek alphabet """
            state_id = 'Γ'

        gamma = Gamma(resource=Mock(), state_manager=Mock())

        self.assertEqual(Gamma.state_id, 'Γ')
        self.assertEqual(gamma.state_id, 'Γ')
        self.assertEqual(Gamma.description, "The third letter of the greek alphabet")
        self.assertEqual(gamma.description, "The third letter of the greek alphabet")

    def test_state_enum(self):
        """
        Test the ResourceState.Enum helper class
        """
        class StateSet(ResourceState.Enum):
            """ Enum class """
            class StateA(ResourceState):
                """ StateA """
                state_id = 'a'

            class StateB(ResourceState):
                """ StateB """
                state_id = 'b'

            class Other:
                """ Other object - not a state """

        self.assertIsInstance(StateSet.states, tuple)
        self.assertCountEqual(StateSet.states, [StateSet.StateA, StateSet.StateB])

        # And with inheritance:

        class MoreStates(StateSet):
            """ Inherited enum class """
            class StateC(ResourceState):
                """ StateC """
                state_id = 'c'

        self.assertIsInstance(MoreStates.states, tuple)
        self.assertCountEqual(MoreStates.states, [StateSet.StateA, StateSet.StateB, MoreStates.StateC])


class BaseState(ResourceState):
    """
    The base class for the three test states, State1, State2, and State3
    """


class State1(BaseState):
    """ The first test state """
    state_id = 'state1'
    name = "State 1"


class State2(BaseState):
    """ The second test state """
    state_id = 'state2'
    name = "State 2"


class State3(BaseState):
    """ The third test state """
    state_id = 'state3'
    name = "State 3"


class SimpleResource:
    """
    A simple resource class for test purposes, which has one three-state FSM, 'state'.
    """
    state = ResourceStateDescriptor(
        state_classes=(State1, State2, State3),
        default_state=State1,
    )
    # Define some transitions:
    done_one = state.transition(from_states=State1, to_state=State2)
    done_two = state.transition(from_states=State2, to_state=State3)
    reset_to_one = state.transition(from_states=(State2, State3), to_state=State1)
    reset_to_one_alt = state.transition(from_states=BaseState, to_state=State1)

    return_value = True  # Change this to change the expected return value of most of these methods.

    @state.only_for(State1)
    def method_one(self):
        """ A method that only can be called in state 1 """
        return self.return_value

    @state.only_for(State1)
    def method_one_with_args(self, a, b, c):  # pylint: disable=no-self-use,invalid-name
        """ A method that only can be called in state 1 """
        return (a * 1) + (b * 2) + (c * 3)

    @state.only_for(State2)
    def method_two(self):
        """ A method that only can be called in state 2 """
        return self.return_value

    @state.only_for(State1, State3)
    def method_odd(self):
        """ A method that only can be called in states 1 or 3 """
        return self.return_value

    @property
    @state.only_for(State1)
    def prop_one(self):
        """ A property whose value is only available in state 1 """
        return self.return_value

    @property
    @state.only_for(State2, State3)
    def prop_two(self):
        """ A property whose value is only available in state 2 or 3 """
        return self.return_value

    @state.only_for(State1, State2)
    def increment_state(self):
        """ Increment the state """
        if isinstance(self.state, State1):
            self.done_one()
        else:
            self.done_two()


class SimpleResourceTestCase(TestCase):
    """
    ResourceStateDescriptor tests that use the SimpleResource class
    """
    make_resource = SimpleResource

    def test_comparison_to_state_class(self):
        """
        Test the overloaded comparison operators
        """
        res1 = self.make_resource()
        res2 = self.make_resource()
        self.assertEqual(res1.state, State1)
        self.assertEqual(res2.state, State1)
        self.assertNotEqual(res1.state, BaseState)
        self.assertNotEqual(res1.state, State2)
        self.assertNotEqual(res2.state, State2)
        self.assertTrue(res1.state == State1)
        self.assertFalse(res1.state != State1)

    def test_comparison_to_state_instance(self):
        """
        Test the syntactic sugar that allows comparing ResourceState instances.
        """
        res1 = self.make_resource()
        res2 = self.make_resource()
        self.assertEqual(res1.state, State1)
        self.assertEqual(res2.state, State1)
        # States are also equal if their instances are equal:
        self.assertEqual(res1.state, res1.state)
        self.assertEqual(hash(res1.state), hash(res1.state))
        # States are also equal if they are the same type but different resources:
        self.assertEqual(res1.state, res2.state)
        self.assertEqual(hash(res1.state), hash(res2.state))
        res2.increment_state()
        self.assertNotEqual(res1.state, res2.state)
        self.assertNotEqual(hash(res1.state), hash(res2.state))

    def test_comparison_to_related_states(self):
        """
        Test that states do not compare as equal to parent/child states.
        (Use proper isinstance() / issubclass() syntax if you want to check that.)
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)
        base_state = BaseState(Mock(), Mock())

        class ChildOverrideState(State1):
            """ A child of State1 with the same state_id """

        child_state = ChildOverrideState(Mock(), Mock())

        # It's OK for two states that exist to have the same state_id, as long as they are not
        # both used by the same ResourceStateDescriptor.
        self.assertEqual(res.state.state_id, child_state.state_id)

        # The syntactic sugar for comparison should not consider parent or child states equal.
        # (Even if their state_id is the same.)
        # The semantics of this are debatable, but this way is hopefully more clear and consistent.
        self.assertNotEqual(res.state, base_state)
        self.assertNotEqual(hash(res.state), hash(base_state))
        self.assertNotEqual(res.state, child_state)
        self.assertNotEqual(hash(res.state), hash(child_state))

    def test_default_state(self):
        """
        Test that when a resource is initialized it uses the correct default state.
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)
        self.assertEqual(res.state.name, "State 1")

    def test_one_of(self):
        """
        Test the one_of() helper method
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)
        self.assertTrue(res.state.one_of(State1))
        self.assertTrue(res.state.one_of(State2, State1, State3))
        self.assertFalse(res.state.one_of(State2, State3))

    def test_unique_state_ids(self):
        """
        It is forbidden to declare a ResourceStateDescriptor which has multiple states with the
        same state_id.
        """
        with self.assertRaisesRegex(AssertionError, "A resource's states must each have a unique state_id"):
            ResourceStateDescriptor(state_classes=(State1, State1, State3), default_state=State1)

        class ChildState(State2):
            """ A child of state2 with the same state_id """

        with self.assertRaisesRegex(AssertionError, "A resource's states must each have a unique state_id"):
            ResourceStateDescriptor(state_classes=(State1, State2, ChildState), default_state=State1)

    def test_missing_state_ids(self):
        """
        It is forbidden to declare ResourceStateDescriptor using states that have no state_id
        """
        self.assertEqual(BaseState.state_id, None)
        with self.assertRaisesRegex(AssertionError, "A resource's states must each declare a state_id string"):
            ResourceStateDescriptor(state_classes=(State1, BaseState), default_state=State1)

    def test_cannot_assign_state(self):
        """
        Ensure that a resource's state cannot be changed by assigning to the state attribute.
        (Instead, a transition should be used.)
        """
        res = self.make_resource()
        expected_message = "You cannot assign to a state machine attribute to change the state."
        with self.assertRaisesRegex(AttributeError, expected_message):
            res.state = State2

    def test_mutator(self):
        """
        Test an exmaple method that changes the state.
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)
        res.increment_state()
        self.assertEqual(res.state, State2)
        res.increment_state()
        self.assertEqual(res.state, State3)

    def test_disallowed_transition(self):
        """
        Test that disallowed transitions will raise an exception.
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)
        expected_message = "This transition cannot be used to move from State 1 to State 3"
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.done_two()
        expected_message = "This transition cannot be used to move from State 1 to State 1"
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.reset_to_one()

    def test_multiple_from_states(self):
        """
        Test that transitions can be defined with multiple from_states.
        """
        res = self.make_resource()
        res.increment_state()
        res.increment_state()
        self.assertEqual(res.state, State3)
        res.reset_to_one()
        self.assertEqual(res.state, State1)

    def test_inherited_from_states(self):
        """
        Test that transitions can be defined with from_states specifying a base class or mixin.
        """
        res = self.make_resource()
        res.increment_state()
        self.assertEqual(res.state, State2)
        res.reset_to_one_alt()
        self.assertEqual(res.state, State1)

    def test_method_only_for(self):
        """
        Test that the @state.only_for() decorator works when used to decorate methods.
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)

        # In State 1, we can call method_one():
        res.return_value = 'A'
        self.assertEqual(res.method_one(), 'A')
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_one.is_available(), True) #pylint: disable=no-member

        # In State 1, we can call method_one_with_args():
        self.assertEqual(res.method_one_with_args(4, 5, c=6), 32)
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_one_with_args.is_available(), True) #pylint: disable=no-member

        # But not method_two()
        expected_message = "The method 'method_two' cannot be called in this state \\(State 1 / State1\\)."
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.method_two()
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_two.is_available(), False) #pylint: disable=no-member

        # In State 1, we can call method_odd():
        res.return_value = 'B'
        self.assertEqual(res.method_odd(), 'B')
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_odd.is_available(), True) #pylint: disable=no-member

        # Go to State 2:
        res.increment_state()
        self.assertEqual(res.state, State2)

        expected_message = "The method 'method_one' cannot be called in this state \\(State 2 / State2\\)."
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.method_one()
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_one.is_available(), False) #pylint: disable=no-member

        res.return_value = 'C'
        self.assertEqual(res.method_two(), 'C')
        # TODO: Why do we need to disable no-member for `is_available`?
        self.assertEqual(res.method_two.is_available(), True) #pylint: disable=no-member

    def test_property_only_for(self):
        """
        Test that the @state.only_for() decorator works with the @property decorator.
        """
        res = self.make_resource()
        self.assertEqual(res.state, State1)

        # In State 1, we can access .prop_one:
        res.return_value = 'A'
        self.assertEqual(res.prop_one, 'A')
        res.return_value = 'B'
        self.assertEqual(res.prop_one, 'B')

        # But not .prop_two:
        expected_message = "The method 'prop_two' cannot be called in this state \\(State 1 / State1\\)."
        with self.assertRaisesRegex(WrongStateException, expected_message):
            dummy = res.prop_two


class DjangoResource:
    """
    Same as SimpleResource but django-backed
    """
    state = ModelResourceStateDescriptor(
        state_classes=(State1, State2, State3),
        default_state=State1,
        model_field_name='backing_field',
    )

    backing_field = models.CharField(max_length=100, choices=state.model_field_choices)

    # Define some transitions:
    done_one = state.transition(from_states=State1, to_state=State2)
    done_two = state.transition(from_states=State2, to_state=State3)
    reset_to_one = state.transition(from_states=(State2, State3), to_state=State1)
    reset_to_one_alt = state.transition(from_states=BaseState, to_state=State1)

    return_value = True  # Change this to change the expected return value of most of these methods.

    @state.only_for(State1)
    def method_one(self):
        """ A method that only can be called in state 1 """
        return self.return_value

    @state.only_for(State1)
    def method_one_with_args(self, a, b, c):  # pylint: disable=no-self-use,invalid-name
        """ A method that only can be called in state 1 """
        return (a * 1) + (b * 2) + (c * 3)

    @state.only_for(State2)
    def method_two(self):
        """ A method that only can be called in state 2 """
        return self.return_value

    @state.only_for(State1, State3)
    def method_odd(self):
        """ A method that only can be called in states 1 or 3 """
        return self.return_value

    @property
    @state.only_for(State1)
    def prop_one(self):
        """ A property whose value is only available in state 1 """
        return self.return_value

    @property
    @state.only_for(State2, State3)
    def prop_two(self):
        """ A property whose value is only available in state 2 or 3 """
        return self.return_value

    @state.only_for(State1, State2)
    def increment_state(self):
        """ Increment the state """
        if isinstance(self.state, State1):
            self.done_one()
        else:
            self.done_two()


class DjangoResourceTest(SimpleResourceTestCase):
    """
    Run the same tests as in SimpleResourceTestCase, but using DjangoResource.
    """
    make_resource = DjangoResource
