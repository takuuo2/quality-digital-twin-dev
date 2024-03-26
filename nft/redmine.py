import datetime
from redminelib import Redmine

''' 
Redmine API でチケット自動発行
--- 未完成 ---
'''
redmine = Redmine('http://172.21.40.30:3000', username='rfukuta', password='Reiya/5/7')
issue = redmine.issue.new()
issue.project_id = 23
issue.subject = '色覚障害者に対するアクセシビリティテスト'  #チケットのタイトル
issue.tracker_id = 5   #トラッカー
issue.description = 'チケットの詳細説明' #詳細説明
issue.status_id = 1      #ステータス
issue.priority_id = 4    #優先度
issue.assigned_to_id = 8 #担当者のID
#issue.watcher_user_ids = [1] # ウォッチするユーザのID
#issue.parent_issue_id = 12     # 親チケットのID
issue.start_date = datetime.date.today() #開始日
issue.due_date = datetime.date.today() + datetime.timedelta(days=3)   #期日
issue.estimated_hours = 5   # 予想工数
issue.done_ratio = 0
issue.custom_fields = [{'id': '9', 'value': '36'}]
issue.save()

