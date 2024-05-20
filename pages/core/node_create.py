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
        self.logs = []  # logテーブルの情報を保持するためのリスト

    @staticmethod
    def fetch_all_nodes():
        # データベースから全ての品質ノードを取得するメソッド
        nodes = []
        try:
            connector = write_db.get_connector()
            cursor = connector.cursor()
            cursor.execute('SELECT * FROM qualitynode')
            records = cursor.fetchall()

            for record in records:
                nid, pid, cid, type, subtype, content, achievement = record
                node = QualityNode(nid, pid, cid, type, subtype, content, achievement)
                
                # logテーブルの情報を取得し、ノードのlogsリストに追加
                cursor.execute('SELECT * FROM log WHERE NID = %s', (nid,))
                logs = cursor.fetchall()
                for log in logs:
                    node.logs.append(log)

                nodes.append(node)

        except (Exception, Error) as error:
            print('PostgreSQLへの接続時のエラーが発生しました:', error)

        finally:
            cursor.close()
            connector.close()

        return nodes


class QualityRequirement(QualityNode):
    @staticmethod
    def get_quality_requirements():
        # 全ての品質要求ノードを返すメソッド
        all_nodes = QualityNode.fetch_all_nodes()  # 全てのノードを取得
        return [node for node in all_nodes if node.type == 'REQ']  # 品質要求ノードのみを返す


class QualityImplementation(QualityNode):
    @staticmethod
    def get_quality_implementations():
        # 全ての品質実現ノードを返すメソッド
        all_nodes = QualityNode.fetch_all_nodes()  # 全てのノードを取得
        return [node for node in all_nodes if node.type == 'IMP']  # 品質実現ノードのみを返す


class QualityActivity(QualityNode):
    @staticmethod
    def get_quality_activities():
        # 全ての品質活動ノードを返すメソッド
        all_nodes = QualityNode.fetch_all_nodes()  # 全てのノードを取得
        return [node for node in all_nodes if node.type == 'ACT']  # 品質活動ノードのみを返す

    @staticmethod
    def get_non_achieved_activities():
        # achievementが1ではない品質活動ノードを返すメソッド
        activities = QualityActivity.get_quality_activities()
        return [activity for activity in activities if activity.achievement != 1]

