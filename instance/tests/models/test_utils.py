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

from instance.models.utils import ResourceState, ResourceStateDescriptor, WrongStateException

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
            """ The first letter of the greek alphabet """
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

        self.assertCountEqual(StateSet.states, [StateSet.StateA, StateSet.StateB])


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

    return_value = True  # Change this to change the expected return value of each method.

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
    def test_comparison_to_state_class(self):
        """
        Test the overloaded comparison operators
        """
        res1 = SimpleResource()
        res2 = SimpleResource()
        self.assertEqual(res1.state, State1)
        self.assertEqual(res2.state, State1)
        self.assertNotEqual(res1.state, State2)
        self.assertNotEqual(res2.state, State2)
        self.assertTrue(res1.state == State1)
        self.assertFalse(res1.state != State1)

    def test_comparison_to_state_instance(self):
        """
        Test the syntactic sugar that allows comparing ResourceState instances.
        """
        res1 = SimpleResource()
        res2 = SimpleResource()
        self.assertEqual(res1.state, State1)
        self.assertEqual(res2.state, State1)
        # States are also equal if their instances are equal:
        self.assertEqual(res1.state, res1.state)
        # States are also equal if they are the same type but different resources:
        self.assertEqual(res1.state, res2.state)
        res2.increment_state()
        self.assertNotEqual(res1.state, res2.state)

    def test_default_state(self):
        """
        Test that when a resource is initialized it uses the correct default state.
        """
        res = SimpleResource()
        self.assertEqual(res.state, State1)
        self.assertEqual(res.state.name, "State 1")

    def test_one_of(self):
        """
        Test the one_of() helper method
        """
        res = SimpleResource()
        self.assertEqual(res.state, State1)
        self.assertTrue(res.state.one_of(State1))
        self.assertTrue(res.state.one_of(State2, State1, State3))
        self.assertFalse(res.state.one_of(State2, State3))

    def test_cannot_assign_state(self):
        """
        Ensure that a resource's state cannot be changed by assigning to the state attribute.
        (Instead, a transition should be used.)
        """
        res = SimpleResource()
        expected_message = "You cannot assign to a state machine attribute to change the state."
        with self.assertRaisesRegex(AttributeError, expected_message):
            res.state = State2

    def test_mutator(self):
        """
        Test an exmaple method that changes the state.
        """
        res = SimpleResource()
        self.assertEqual(res.state, State1)
        res.increment_state()
        self.assertEqual(res.state, State2)
        res.increment_state()
        self.assertEqual(res.state, State3)

    def test_disallowed_transition(self):
        """
        Test that disallowed transitions will raise an exception.
        """
        res = SimpleResource()
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
        res = SimpleResource()
        res.increment_state()
        res.increment_state()
        self.assertEqual(res.state, State3)
        res.reset_to_one()
        self.assertEqual(res.state, State1)

    def test_inherited_from_states(self):
        """
        Test that transitions can be defined with from_states specifying a base class or mixin.
        """
        res = SimpleResource()
        res.increment_state()
        self.assertEqual(res.state, State2)
        res.reset_to_one_alt()
        self.assertEqual(res.state, State1)

    def test_method_only_for(self):
        """
        Test that the @state.only_for() decorator works when used to decorate methods.
        """
        res = SimpleResource()
        self.assertEqual(res.state, State1)

        # In State 1, we can call method_one():
        res.return_value = 'A'
        self.assertEqual(res.method_one(), 'A')
        self.assertEqual(res.method_one.is_available(), True)

        # In State 1, we can call method_one_with_args():
        self.assertEqual(res.method_one_with_args(4, 5, c=6), 32)
        self.assertEqual(res.method_one_with_args.is_available(), True)

        # But not method_two()
        expected_message = "The method 'method_two' cannot be called in this state \\(State 1 / State1\\)."
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.method_two()
        self.assertEqual(res.method_two.is_available(), False)

        # In State 1, we can call method_odd():
        res.return_value = 'B'
        self.assertEqual(res.method_odd(), 'B')
        self.assertEqual(res.method_odd.is_available(), True)

        # Go to State 2:
        res.increment_state()
        self.assertEqual(res.state, State2)

        expected_message = "The method 'method_one' cannot be called in this state \\(State 2 / State2\\)."
        with self.assertRaisesRegex(WrongStateException, expected_message):
            res.method_one()
        self.assertEqual(res.method_one.is_available(), False)

        res.return_value = 'C'
        self.assertEqual(res.method_two(), 'C')
        self.assertEqual(res.method_two.is_available(), True)

    def test_property_only_for(self):
        """
        Test that the @state.only_for() decorator works with the @property decorator.
        """
        res = SimpleResource()
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
