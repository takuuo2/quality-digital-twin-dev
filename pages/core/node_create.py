# from psycopg2 import Error
# from . import write_db


# class QualityNode:
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution):
#         self.nid = nid
#         self.pid = pid
#         self.parents = parents
#         self.children = children
#         self.type = type
#         self.subtype = subtype
#         self.task = task
#         self.achievement = achievement
#         self.contribution = contribution
    
#     @staticmethod
#     def get_node_support():
#         node_support = []
#         connector = None
#         cursor = None
#         try:
#             connector = write_db.get_connector()
#             cursor = connector.cursor()
#             cursor.execute('SELECT source, destination, contribution FROM support')
#             node_support = cursor.fetchall()
#         except (Exception, Error) as error:
#             print('PostgreSQLへの接続時のエラーが発生しました:', error)
#         finally:
#             if cursor:
#                 cursor.close()
#             if connector:
#                 connector.close()
#         return node_support

#     @classmethod
#     def assign_support_to_nodes(cls, nodes, node_support):
#         # ノードの辞書を作成して、nidで検索しやすくする
#         node_dict = {node.nid: node for node in nodes}
#         #デバック用変数
#         # count = 0
#         for node in nodes:
#             #デバック用
#             # print(node)
#             # count += 1
#             # if count == 20:
#             #     break
#             # destinationがnodeのnidと等しいものを探す
#             for support in node_support:
#                 destination, source, contribution = support
#                 if destination == node.nid:
#                     # print(source)
#                     # print(node_dict[source])
#                     while source in node_dict and node_dict[source].type != 'REQ':
#                         # sourceの値をdestinationに移して再検索
#                         next_source = next((s[1] for s in node_support if s[0] == source), None)
#                         if next_source is None:
#                             #デバック用
#                             # print('miss')
#                             break
#                         source = next_source

#                     if source in node_dict and node_dict[source].type == 'REQ':
#                         node.parents.append(source)
#                         node.contribution.append(contribution)

#             # sourceがnodeのnidと等しいものを探す
#             for support in node_support:
#                 destination, source, contribution = support
#                 if source == node.nid:
#                     node.children.append(destination)
#             #デバック用
#             # print(f"Node {node.nid} parents: {node.parents}, children: {node.children}, type: {node.type}")
        
#         return nodes

    
    
#     @staticmethod
#     def fetch_all_nodes():
#         nodes = []
#         connector = None
#         cursor = None
#         try:
#             connector = write_db.get_connector()
#             cursor = connector.cursor()
#             cursor.execute('SELECT * FROM qualitynode')
#             records = cursor.fetchall()
#             node_support = QualityNode.get_node_support()
#             for record in records:
#                 nid, pid, cid, type, subtype, content, achievement = record
#                 parents = []
#                 children = []
#                 contribution = []
#                 task = content #仮でcontentを代入

#                 if type == 'ACT':
#                     node = QualityActivity(nid, pid, parents, children, type, subtype, task, achievement, contribution, is_manual=None)
#                 elif type == 'REQ':
#                     node = QualityRequirement(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text=None)
#                 elif type == 'IMP':
#                     node = QualityImplementation(nid, pid, parents, children, type, subtype, task, achievement, contribution, description=None)
#                 else:
#                     node = QualityNode(nid, pid, parents, children, type, subtype, task, achievement, contribution)
#                 nodes.append(node)

#             nodes = QualityNode.assign_support_to_nodes(nodes, node_support)

#         except (Exception, Error) as error:
#             print('PostgreSQLへの接続時のエラーが発生しました:', error)

#         finally:
#             if cursor:
#                 cursor.close()
#             if connector:
#                 connector.close()

#         return nodes

#     def dispatch(self):
#         pass


# class QualityRequirement(QualityNode):
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text):
#         super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
#         self.req_text = req_text

#     #デバック用
#     def __str__(self):
#         return f'QualityRequirement(nid={self.nid}, type={self.type})'
#     @staticmethod
#     def get_quality_requirements():
#         all_nodes = QualityNode.fetch_all_nodes()
#         return [node for node in all_nodes if node.type == 'REQ']
    



# class QiURequirement(QualityRequirement):
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text, qiu_char):
#         super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text)
#         self.qiu_char = qiu_char


# class PQRequirement(QualityRequirement):
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text, pq_char):
#         super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution, req_text)
#         self.pq_char = pq_char


# class QualityImplementation(QualityNode):
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, description):
#         super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
#         self.description = description

#     #デバック用
#     def __str__(self):
#         return f'QualityImplementation(nid={self.nid}, type={self.type})'
#     @staticmethod
#     def get_quality_implementations():
#         all_nodes = QualityNode.fetch_all_nodes()
#         return [node for node in all_nodes if node.type == 'IMP']


# class Function(QualityImplementation):
#     pass


# class Architecture(QualityImplementation):
#     pass


# class QualityActivity(QualityNode):
#     def __init__(self, nid, pid, parents, children, type, subtype, task, achievement, contribution, is_manual):
#         super().__init__(nid, pid, parents, children, type, subtype, task, achievement, contribution)
#         self.is_manual = is_manual

#     #デバック用
#     def __str__(self):
#         return f'QualityActivity(nid={self.nid}, type={self.type})'
#     @staticmethod
#     def get_quality_activities():
#         all_nodes = QualityNode.fetch_all_nodes()
#         return [node for node in all_nodes if node.type == 'ACT']

#     @staticmethod
#     def get_non_achieved_activities():
#         activities = QualityActivity.get_quality_activities()
#         return [activity for activity in activities if activity.achievement != 1]

#     def get_bottom_req(self):
#         pass


# class Task:
#     def __init__(self, tid, name, nid, cost, parameter):
#         self.tid = tid
#         self.name = name
#         self.nid = nid
#         self.cost = cost
#         self.parameter = parameter

#     def calculate_cost(self):
#         return self.cost


# class ManualTask(Task):
#     def __init__(self, tid, name, nid, cost, parameter, assigned_to):
#         super().__init__(tid, name, nid, cost, parameter)
#         self.assigned_to = assigned_to


# class FuncTesting(ManualTask):
#     pass


# class NonFuncTesting(ManualTask):
#     def calculate_cost(self):
#         # 具体的なコスト計算ロジックをここに記述
#         return self.cost



##データベース更新用edit.pyに配置
# def create_list_from_activities(activities, nodes):
#     result = []
    
#     # ノードの辞書を作成して、nidで検索しやすくする
#     node_dict = {node.nid: node for node in nodes}
    
#     connector = None
#     cursor = None
    
#     try:
#         connector = write_db.get_connector()
#         cursor = connector.cursor()
        
#         for activity in activities:
#             content = activity.task
#             parent_statement = None
#             parent_subchar = None
#             nid = activity.nid  # アクティビティの nid を取得
            
#             # 親ノードの情報を取得
#             if activity.parents:
#                 parent_nid = activity.parents[0]
#                 parent_node = node_dict.get(parent_nid)
#                 if parent_node and isinstance(parent_node.task, dict):
#                     parent_statement = parent_node.task.get('statement')
#                     parent_subchar = parent_node.task.get('subchar')

#             if isinstance(content, dict) and 'subchar' in content:
#                 result.append({
#                     'nid': nid, 
#                     'name': content['subchar'], 
#                     'cost': 5, 
#                     'parent': parent_subchar, 
#                     'statement': parent_statement
#                 })
                
#                 # タスクテーブルにデータを挿入
#                 cursor.execute(
#                     '''
#                     INSERT INTO task (tname, nid, cost, parameter)
#                     VALUES (%s, %s, %s, %s)
#                     ''', 
#                     (
#                         content['subchar'],  # tname
#                         nid,                 # nid
#                         5,                   # cost
#                         '{"example": "value"}'  # parameter (例としてJSON文字列)
#                     )
#                 )
        
#         connector.commit()  # 変更をコミット
#     except (Exception, Error) as error:
#         print('PostgreSQLへの接続時のエラーが発生しました:', error)
#         if connector:
#             connector.rollback()  # エラー発生時にロールバック
#     finally:
#         if cursor:
#             cursor.close()
#         if connector:
#             connector.close()

#     return result





#  @callback(
#     [Output({'type': 'card', 'nid': ALL}, 'style'),
#      Output('total-cost', 'children'),
#      Output({'type': 'dropdown', 'nid': ALL}, 'style'),
#      Output('task-table', 'data'), 
#      Output('member-table', 'data')],  
#     [Input({'type': 'card', 'nid': ALL}, 'n_clicks'),
#      Input({'type': 'dropdown', 'nid': ALL}, 'value')],
#     [State({'type': 'card', 'nid': ALL}, 'style'),
#      State({'type': 'dropdown', 'nid': ALL}, 'style'),
#      State({'type': 'dropdown', 'nid': ALL}, 'id')]
# )
# def update_selection(n_clicks, selected_values, card_styles, dropdown_styles, dropdown_ids):
#     if not n_clicks:
#         raise PreventUpdate
#     total_cost = 0
#     new_card_styles = []
#     new_dropdown_styles = []

#     # リストの長さを合わせる
#     num_items = len(n_clicks)
#     if len(card_styles) < num_items:
#         card_styles.extend([{} for _ in range(num_items - len(card_styles))])
#     if len(dropdown_styles) < num_items:
#         dropdown_styles.extend([{} for _ in range(num_items - len(dropdown_styles))])

#     for i, clicks in enumerate(n_clicks):
#         if clicks and clicks % 2 == 1:
#             card_styles[i]['backgroundColor'] = '#d3d3d3'
#             dropdown_styles[i]['display'] = 'block'  # プルダウンを表示
#             total_cost += list_ex[i]['cost']
#         else:
#             card_styles[i]['backgroundColor'] = 'white'
#             dropdown_styles[i]['display'] = 'none'  # プルダウンを非表示
#         new_card_styles.append(card_styles[i])
#         new_dropdown_styles.append(dropdown_styles[i])
    
#     # プロジェクトIDに基づいてメンバーをフィルタリング
#     filtered_members = [
#         member for member in members
#         if str(member["pid"]) == current_pid
#     ]
    
#     # タスクの割り当てと同時にメンバーのused_resourceを更新
#     for i, value in enumerate(selected_values):
#         if value:
#             member_mid = next((member['mid'] for member in filtered_members if member['mname'] == value), None)
#             if member_mid:
#                 task_nid = dropdown_ids[i]['nid']
#                 search_task = next((t for t in tasks if t.nid == task_nid), None)  # tasksからnidが一致するタスクを探す
#                 if search_task:
#                     # 元々の割り当てを削除
#                     for assignment in assignments:
#                         if assignment.tid == search_task.tid:
#                             member = next((member for member in filtered_members if member['mid'] == assignment.mid), None)
#                             if member:
#                                 member['used_resource'] -= search_task.cost
#                             assignments.remove(assignment)
#                 else:
#                     # 新しいタスクを作成してtasksに追加
#                     if tasks:
#                         new_tid = tasks[-1].tid + 1
#                     else:
#                         new_tid = None
#                     new_tname = list_ex[i]['name']  # 対応するカードのnameを取得
#                     new_cost = list_ex[i]['cost']   # 対応するカードのcostを取得
#                     new_parameter = json.dumps({"example": "value"})  # 必要に応じて適切なパラメータを設定
#                     search_task = task.Task(new_tid, new_tname, task_nid, new_cost, new_parameter)
#                     tasks.append(search_task)
#                 new_assignment = task.TaskAssignment(aid=None, tid=search_task.tid, mid=member_mid)
#                 assignments.append(new_assignment)
#                 member = next((member for member in filtered_members if member['mid'] == member_mid), None)
#                 if member:
#                     member['used_resource'] += search_task.cost
                
    
#     # task-tableのデータ更新
#     table_data = []
#     for member in filtered_members:
#         assigned_tasks = []
#         for assignment in assignments:
#             if assignment.mid == member["mid"]:
#                 assigned_task_name = next((task.tname for task in tasks if task.tid == assignment.tid), "")
#                 if assigned_task_name:
#                     assigned_tasks.append(assigned_task_name)
        
#         # リストをカンマ区切りの文字列に変換
#         assigned_tasks_str = ", ".join(assigned_tasks) if assigned_tasks else ""
#         table_data.append({"mname": member["mname"], "AssignedTask": assigned_tasks_str})

#     # member-tableのデータ更新
#     member_table_data = [
#         {
#             "mname": member["mname"],
#             "sprint_resource": member["sprint_resource"],
#             "used_resource": member["used_resource"],
#             "RemainingResource": member['sprint_resource'] - member['used_resource']
#         }
#         for member in filtered_members
#     ]
    
#     # カードと割り当てられたタスクを比較し、割り当てられたタスクがあればカードのスタイルを変更する
#     for i, card in enumerate(new_card_styles):
#         card_nid = list_ex[i]['nid']  # カードのnidを取得
#         for assignment in assignments:
#             assigned_task = next((task for task in tasks if task.tid == assignment.tid), None)
#             if assigned_task and assigned_task.nid == card_nid:
#                 card['backgroundColor'] = '#d3d3d3'  # カードの背景色を変更
#                 # 割り当て済みの人が選択されているプルダウンを表示し、選択された状態にする
#                 assigned_member = next((member for member in filtered_members if member['mid'] == assignment.mid), None)
#                 if assigned_member:
#                     dropdown_id = {'type': 'dropdown', 'nid': card_nid}
#                     dropdown_index = dropdown_ids.index(dropdown_id)
#                     new_dropdown_styles[dropdown_index]['display'] = 'block'
#                     new_dropdown_styles[dropdown_index]['value'] = assigned_member['mname']
#                     new_dropdown_styles[dropdown_index]['placeholder'] = assigned_member['mname']

#     # 合計コストと残りのコストを計算する
#     total_cost_mh = total_cost
#     total_sprint_resource = sum(member['sprint_resource'] for member in member_table_data)
#     remaining_resource = total_sprint_resource - total_cost_mh

#     return new_card_styles, f"Total Cost: {total_cost_mh} MH", new_dropdown_styles, table_data, member_table_data, f"メンバーの総スプリントリソース: {total_sprint_resource} MH, 使用可能コスト残量: {remaining_resource} MH"



# # メンバーの合計リソースを計算して表示するコールバック
# @callback(
#     [Output('total-person-cost', 'children'),
#      Output('remaining-person-cost', 'children')],
#     [Input('total-cost', 'children')],
#     [State('member-table', 'data')]
# )
# def update_person_cost(total_cost_text, member_data):
#     if not total_cost_text or not member_data:
#         raise PreventUpdate

#     total_cost_mh = int(total_cost_text.split(":")[1].strip().split()[0])
#     total_sprint_resource = sum(member['sprint_resource'] for member in member_data)
#     remaining_resource = total_sprint_resource - total_cost_mh

#     return (
#         f"メンバーの総スプリントリソース: {total_sprint_resource} MH",
#         f"使用可能コスト残量: {remaining_resource} MH"
#     )
