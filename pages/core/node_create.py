from psycopg2 import Error
from . import write_db

class QualityNode:
    def __init__(self, nid, pid, cid, type, subtype, content, achievement):
        self.nid = nid
        self.pid = pid
        self.cid = cid
        self.type = type
        self.subtype = subtype
        self.content = content
        self.achievement = achievement

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

            for record in records:
                nid, pid, cid, type, subtype, content, achievement = record
                if type == 'ACT':
                    node = QualityActivity(nid, pid, cid, type, subtype, content, achievement)
                else:
                    node = QualityNode(nid, pid, cid, type, subtype, content, achievement)
                nodes.append(node)

        except (Exception, Error) as error:
            print('PostgreSQLへの接続時のエラーが発生しました:', error)

        finally:
            if cursor:
                cursor.close()
            if connector:
                connector.close()

        return nodes

class QualityRequirement(QualityNode):
    @staticmethod
    def get_quality_requirements():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'REQ']

    @staticmethod
    def get_requirement_by_cid(cid):
        requirements = QualityRequirement.get_quality_requirements()
        for req in requirements:
            if req.cid == cid:
                return req
        return None

class QualityImplementation(QualityNode):
    @staticmethod
    def get_quality_implementations():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'IMP']

class QualityActivity(QualityNode):
    def __init__(self, nid, pid, cid, type, subtype, content, achievement, task=None):
        super().__init__(nid, pid, cid, type, subtype, content, achievement)
        self.task = task

    @staticmethod
    def get_quality_activities():
        all_nodes = QualityNode.fetch_all_nodes()
        return [node for node in all_nodes if node.type == 'ACT']

    @staticmethod
    def get_non_achieved_activities():
        activities = QualityActivity.get_quality_activities()
        return [activity for activity in activities if activity.achievement != 1]

    def dispatch(self):
        pass
