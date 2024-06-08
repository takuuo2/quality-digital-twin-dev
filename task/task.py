class Task:
    def __init__(self, tid, name, nid, cost, parameter):
        self.tid = tid
        self.name = name
        self.nid = nid
        self.cost = cost
        self.parameter = parameter

    def calculate_cost(self):
        # Implementation of cost method
        pass  # Placeholder for the method implementation

class ManualTask(Task):
    def __init__(self, tid, name, nid, cost, parameter, assigned_to):
        super().__init__(tid, name, nid, cost, parameter)
        self.assigned_to = assigned_to

class FuncTesting(ManualTask):
    pass


class NonFuncTesting(Task):
    def cost(self):
        # Implementation of cost method for NonFuncTesting
        pass  # Placeholder for the method implementation