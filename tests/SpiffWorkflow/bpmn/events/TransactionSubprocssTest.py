from SpiffWorkflow import TaskState
from SpiffWorkflow.bpmn import BpmnWorkflow

from ..BpmnWorkflowTestCase import BpmnWorkflowTestCase

__author__ = 'michaelc'


class TransactionSubprocessTest(BpmnWorkflowTestCase):

    def setUp(self):
        self.spec, self.subprocesses = self.load_workflow_spec('transaction.bpmn', 'Main_Process')
        self.workflow = BpmnWorkflow(self.spec, self.subprocesses)
        self.workflow.do_engine_steps()

    def testNormalCompletion(self):

        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)
        ready_tasks[0].set_data(**{'value': 'asdf'})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()
        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)
        ready_tasks[0].set_data(**{'quantity': 2})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()
        self.assertIn('value', self.workflow.last_task.data)

        # Check that workflow and next task completed
        subprocess = self.workflow.get_next_task(spec_name='Subprocess')
        self.assertEqual(subprocess.state, TaskState.COMPLETED)
        print_task = self.workflow.get_next_task(spec_name="Activity_Print_Data")
        self.assertEqual(print_task.state, TaskState.COMPLETED)

        # Check that the boundary events were cancelled
        cancel_task = self.workflow.get_next_task(spec_name="Catch_Cancel_Event")
        self.assertEqual(cancel_task.state, TaskState.CANCELLED)
        error_1_task = self.workflow.get_next_task(spec_name="Catch_Error_1")
        self.assertEqual(error_1_task.state, TaskState.CANCELLED)
        error_none_task = self.workflow.get_next_task(spec_name="Catch_Error_None")
        self.assertEqual(error_none_task.state, TaskState.CANCELLED)

    def testSubworkflowCancelEvent(self):

        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)

        # If value == '', we cancel
        ready_tasks[0].set_data(**{'value': ''})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()

        # If the subprocess gets cancelled, verify that data set there does not persist
        self.assertNotIn('value', self.workflow.last_task.data)

        # Check that we completed the Cancel Task
        cancel_task = self.workflow.get_next_task(spec_name="Cancel_Action")
        self.assertEqual(cancel_task.state, TaskState.COMPLETED)

        # And cancelled the remaining tasks
        error_1_task = self.workflow.get_next_task(spec_name="Catch_Error_1")
        self.assertEqual(error_1_task.state, TaskState.CANCELLED)
        error_none_task = self.workflow.get_next_task(spec_name="Catch_Error_None")
        self.assertEqual(error_none_task.state, TaskState.CANCELLED)

        # We should not have this task, as we followed the 'cancel branch'
        print_task = self.workflow.get_tasks(spec_name="Activity_Print_Data")
        self.assertEqual(len(print_task), 1)
        self.assertEqual(print_task[0].state, TaskState.CANCELLED)

    def testSubworkflowErrorCodeNone(self):

        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)
        ready_tasks[0].set_data(**{'value': 'asdf'})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()
        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)

        # If quantity == 0, we throw an error with no error code
        ready_tasks[0].set_data(**{'quantity': 0})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()

        # We formerly checked that subprocess data does not persist, but I think it should persist
        # A boundary event is just an alternate path out of a workflow, and we might need the context
        # of the event in later steps

        # The cancel boundary event should be cancelled
        cancel_task = self.workflow.get_next_task(spec_name="Catch_Cancel_Event")
        self.assertEqual(cancel_task.state, TaskState.CANCELLED)

        # We should catch the None Error, but not Error 1
        error_none_task = self.workflow.get_next_task(spec_name="Catch_Error_None")
        self.assertEqual(error_none_task.state, TaskState.COMPLETED)
        error_1_task = self.workflow.get_next_task(spec_name="Catch_Error_1")
        self.assertEqual(error_1_task.state, TaskState.CANCELLED)

        # Make sure this branch didn't getfollowed
        print_task = self.workflow.get_tasks(spec_name="Activity_Print_Data")
        self.assertEqual(len(print_task), 1)
        self.assertEqual(print_task[0].state, TaskState.CANCELLED)

    def testSubworkflowErrorCodeOne(self):

        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)
        ready_tasks[0].set_data(**{'value': 'asdf'})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()
        ready_tasks = self.workflow.get_tasks(state=TaskState.READY)

        # If quantity < 0, we throw 'Error 1'
        ready_tasks[0].set_data(**{'quantity': -1})
        ready_tasks[0].run()
        self.workflow.do_engine_steps()

        # The cancel boundary event should be cancelled
        # I've removed this check, see previous test for rationale

        # Both boundary events should complete
        error_none_task = self.workflow.get_next_task(spec_name="Catch_Error_None")
        self.assertEqual(error_none_task.state, TaskState.COMPLETED)
        error_1_task = self.workflow.get_next_task(spec_name="Catch_Error_1")
        self.assertEqual(error_1_task.state, TaskState.COMPLETED)

        print_task = self.workflow.get_tasks(spec_name="Activity_Print_Data")
        self.assertEqual(len(print_task), 1)
        self.assertEqual(print_task[0].state, TaskState.CANCELLED)
