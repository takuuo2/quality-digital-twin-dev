from psycopg2 import Error
from . import write_db


class QualityNode:
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution):
        self.nid = nid
        self.pid = pid
        self.parents = parents
        self.children = children
        self.type = type
        self.subtype = subtype
        self.task = task
        self.achievement = achievement
        self.contribution = contribution
    
    @staticmethod
    def get_node_support():
        node_support = []
        connector = None
        cursor = None
        try:
            connector = write_db.get_connector()
            cursor = connector.cursor()
            cursor.execute('SELECT source, destination, contribution FROM support')
            node_support = cursor.fetchall()
        except (Exception, Error) as error:
            print('PostgreSQLへの接続時のエラーが発生しました:', error)
        finally:
            if cursor:
                cursor.close()
            if connector:
                connector.close()
        return node_support

    @classmethod
    def assign_support_to_nodes(cls, nodes, node_support):
        # ノードの辞書を作成して、nidで検索しやすくする
        node_dict = {node.nid: node for node in nodes}
        #デバック用変数
        # count = 0
        for node in nodes:
            #デバック用
            # print(node)
            # count += 1
            # if count == 20:
            #     break
            # destinationがnodeのnidと等しいものを探す
            for support in node_support:
                destination, source, contribution = support
                if destination == node.nid:
                    # print(source)
                    # print(node_dict[source])
                    while source in node_dict and node_dict[source].type != 'REQ':
                        # sourceの値をdestinationに移して再検索
                        next_source = next((s[1] for s in node_support if s[0] == source), None)
                        if next_source is None:
                            print('miss')
                            break
                        source = next_source

                    if source in node_dict and node_dict[source].type == 'REQ':
                        node.parents.append(source)
                        node.contribution.append(contribution)

            # sourceがnodeのnidと等しいものを探す
            for support in node_support:
                destination, source, contribution = support
                if source == node.nid:
                    node.children.append(destination)
            print(f"Node {node.nid} parents: {node.parents}, children: {node.children}, type: {node.type}")
        
        return nodes

    
    
    @staticmethod
    def fetch_all_nodes():
        nodes = []
        connector = None
        cursor = None
        try:
            connector = write_db.get_connector()
            cursor = connector.cursor()
            cursor.execute('SELECT * FROM qualitynode')
            records = cursor.fetchall()
            node_support = QualityNode.get_node_support()
            for record in records:
                nid, pid, cid, type, subtype, content, achievement = record
                parents = []
                children = []
                contribution = []
                task = content #仮でcontentを代入

                if type == 'ACT':
                    node = QualityActivity(nid, pid, parents, children, type, subtype, task, achievement, contribution, is_manual=None)
                elif type == 'REQ':
                    node = QualityRequirement(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text=None)
                elif type == 'IMP':
                    node = QualityImplementation(nid, pid, parents, children, type, subtype, task, achievement, contribution, description=None)
                else:
                    node = QualityNode(nid, pid, parents, children, type, subtype, task, achievement, contribution)
                nodes.append(node)

            nodes = QualityNode.assign_support_to_nodes(nodes, node_support)

        except (Exception, Error) as error:
            print('PostgreSQLへの接続時のエラーが発生しました:', error)

        finally:
            if cursor:
                cursor.close()
            if connector:
                connector.close()

        return nodes

    def dispatch(self):
        pass


class QualityRequirement(QualityNode):
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text):
        super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
        self.req_text = req_text

    #デバック用
    def __str__(self):
        return f'QualityRequirement(nid={self.nid}, type={self.type})'
    @staticmethod
    def get_quality_requirements():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'REQ']
    



class QiURequirement(QualityRequirement):
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text, qiu_char):
        super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text)
        self.qiu_char = qiu_char


class PQRequirement(QualityRequirement):
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text, pq_char):
        super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text)
        self.pq_char = pq_char


class QualityImplementation(QualityNode):
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, description):
        super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
        self.description = description

    #デバック用
    def __str__(self):
        return f'QualityImplementation(nid={self.nid}, type={self.type})'
    @staticmethod
    def get_quality_implementations():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'IMP']


class Function(QualityImplementation):
    pass


class Architecture(QualityImplementation):
    pass


class QualityActivity(QualityNode):
    def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, is_manual):
        super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
        self.is_manual = is_manual

    #デバック用
    def __str__(self):
        return f'QualityActivity(nid={self.nid}, type={self.type})'
    @staticmethod
    def get_quality_activities():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'ACT']

    @staticmethod
    def get_non_achieved_activities():
        activities = QualityActivity.get_quality_activities()
        return [activity for activity in activities if activity.achievement != 1]

    def get_bottom_req(self):
        pass


class Task:
    def __init__(self, tid, name, nid, cost, parameter):
        self.tid = tid
        self.name = name
        self.nid = nid
        self.cost = cost
        self.parameter = parameter

    def calculate_cost(self):
        return self.cost


class ManualTask(Task):
    def __init__(self, tid, name, nid, cost, parameter, assigned_to):
        super().__init__(tid, name, nid, cost, parameter)
        self.assigned_to = assigned_to


class FuncTesting(ManualTask):
    pass


class NonFuncTesting(ManualTask):
    def calculate_cost(self):
        # 具体的なコスト計算ロジックをここに記述
        return self.cost
