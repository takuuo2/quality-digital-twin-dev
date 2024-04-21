import psycopg2
from psycopg2 import Error
import json

#########################################################
# 機能： QDTデータベースのコネクションを得る（内部関数）
# Note：研究室サーバのpostresql/QDT-DBデータベースを固定
#      して使用
#########################################################
def get_connector():
  connector = psycopg2.connect(
    'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user = 'postgres',        
      password = 'selab',  
      host = '172.21.40.30',  
      port = '5432',           
      dbname = 'QDT-DB'
    )
  )
  return connector

#########################################################
# 機能：   SELECT文の実施
# 入力：   select SELECT文， node そのパラメータリスト
# 戻り値： SELECT文の実行結果，Noneの時'none'を返す
# Note：  Select文とそのパラメータを受けて同文を実行
#         不完全な関数か？（要吟味）
#########################################################
def check_db(select, node):
  try:
    connector = get_connector()    
    cursor = connector.cursor()

    cursor.execute(select, (node,))
    row = cursor.fetchone()
    message = row if row is not None else 'none'

  except (Exception, Error) as error:
    print('接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return message

#########################################################
# 機能：  プロジェクトの登録/更新処理 ###
# 入力：  pname プロジェクト名（キー），nsprint スプリント番号，
#          status プロジェクトのステータス 
# 戻り値： None
#########################################################
def write_project(pname, nsprint, status):
  try:
    connector = get_connector()      
    cursor = connector.cursor()

    # プロジェクトの検索
    check_query = '''
            SELECT pid FROM project WHERE pname = %s
          '''
    cursor.execute(check_query, (pname,))
    result = cursor.fetchone()
   
    # プロジェクトがあれば更新，なければ新規登録
    if result is not None: # プロジェクトがある場合
      # 最大のcidを得る
      check_rmax = '''
              SELECT MAX(cid) FROM qualitynode 
              WHERE pid = %s
            '''
      cursor.execute(check_rmax, (result[0],))
      result = cursor.fetchone()

      # 更新処理の実施
      if result == None:
        rmax = 0
      else:
        rmax = result[0]
        update_query = '''
              UPDATE project 
              SET rmax = %s, nsprint = %s, status=%s 
              WHERE pid = %s;
            '''
        cursor.execute(update_query, (rmax, nsprint, status, result[0],))
        connector.commit()  

    else: # プロジェクトがない場合
      # 登録処理の実施
      insert_query = '''
              INSERT INTO project (pname, rmax, nsprint, status) 
              VALUES (%s, %s, %s, %s)
            '''
      cursor.execute(insert_query, (pname, 0, nsprint, status,))
      connector.commit()     

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return None

#########################################################
# 機能：   品質ノードの登録/更新処理 
# 戻り値： None
# Note： 品質ノードは，親の品質ノードをサポートするものとして一括
#        して登録される
# Note： サポートリンクは別途設定する方が正しい（要検討）
#########################################################
def write_node(pid, node_name, type, subtype, content, # 品質ノード
               contribution, destination, achievement, # サポートリンク
               child_nid=None):
  try:
    connector = get_connector()    
    cursor = connector.cursor()

    # 品質ノード(nid)検索
    check_contribution = '''
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                      '''
    cursor.execute(check_contribution, (node_name, pid))
    nid = cursor.fetchone()

    # 同じ品質ノードがある場合は更新，そうでない場合は新規登録
    if nid != None:
      # 品質ノードの更新
      update_query = '''
                    UPDATE qualitynode SET content = %s  
                    WHERE nid = %s;
                  '''
      cursor.execute(update_query, (json.dumps(content), nid[0],))
      connector.commit() 

      # 品質ノードの更新に伴うサポートリンクの更新
      #   品質ノードがサポートしているリンクの検索
      check_contribution = '''
                    SELECT sid
                    FROM support
                    WHERE source = %s;
                  '''
      cursor.execute(check_contribution, (nid[0],))
      sid = cursor.fetchone()
      #   リンクの更新
      update_query1 = '''
                    UPDATE support SET destination = %s,
                    contribution = %s 
                    WHERE sid = %s;
                  '''
      cursor.execute(update_query1, (destination, contribution, sid[0],))
      connector.commit()  
        
    else:
      # typeが合致する品質ノード数を数え＋１する
      # （このやり方では削除され中抜けになったときに重なることがある(要修正）)
      count_query = '''
                SELECT COUNT(*) FROM qualitynode 
                WHERE type LIKE %s AND pid = %s;
              '''
      cursor.execute(count_query, ('%' + type + '%', pid,))
      row = cursor.fetchone()
      cid_count = row[0]+1 if row[0] > 0 else 1

      # 品質ノードの新規登録
      insert_query = '''
                  INSERT INTO qualitynode 
                  (pid, cid, type, subtype, content, achievement) 
                  VALUES (%s, %s, %s, %s, %s, %s)
                '''
      cursor.execute(insert_query, 
           (pid, cid_count, type, subtype, json.dumps(content), achievement,))
      connector.commit()

      # 品質ノード名に合致する品質ノードの検索
      check_contribution = '''
                   SELECT nid
                   FROM qualitynode
                   WHERE content ->> 'subchar' = %s AND pid = %s;
                '''
      cursor.execute(check_contribution, (node_name, pid))
      nid = cursor.fetchone()

      # support書き込み
      insert_query1 = '''
                  INSERT INTO support (source, destination, contribution) 
                  VALUES (%s, %s, %s)
                '''
      record_to_insert1 = (nid[0], destination, contribution)
      cursor.execute(insert_query1, record_to_insert1)
      if child_nid:
          update_query2 = '''
                  UPDATE support SET destination = %s WHERE source = %s;
                '''
          cursor.execute(update_query2, (nid[0], child_nid,))
      connector.commit()  
      print('更新終わり')
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return None

#########################################################
# 機能：  品質ノードの確認 ###
# 入力：  pid プロジェクトID, node_name 品質ノード名（？）
# 戻り値：品質ノードがある場合にはそのレコード，そうでない場合'none'
#########################################################
def check_node(pid, node_name):
  try:
    connector = get_connector()       
    cursor = connector.cursor()

    check_aim = ''' 
            SELECT * FROM qualitynode
            WHERE content ->> 'subchar' = %s AND pid = %s;
          '''
    cursor.execute(check_aim, (node_name, pid,))
    result = cursor.fetchone()
    message = result if result is not None else 'none'

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return message

#########################################################
# 機能：  品質ノード(nid)をサポートする品質ノードのリストを作る
# 戻り値：品質ノードのレコードのリスト
#########################################################
def make_child(nid):
  aim_value=[]

  try:
    connector = get_connector()       
    cursor = connector.cursor()

    children = '''
        SELECT qualitynode.type, qualitynode.content, support.contribution
        FROM qualitynode
        JOIN support ON qualitynode.nid=support.source
        WHERE destination=%s;
      '''
    cursor.execute(children, (nid,))
    aim_value = cursor.fetchall()

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
      cursor.close()
      connector.close()

  return aim_value

#########################################################
# 機能：   指定された品質ノードの前のスプリントでの達成度を得る
# 戻り値：　整数値で返される．前のログがなければ0
# Note ここでroundされる意味があるか精査
#########################################################
def check_achievement_old(pid, node_name):
  try:
    connector = get_connector()    
    cursor = connector.cursor() 

    # 品質ノード名より品質ノードを検索
    check_contribution = '''
              SELECT nid
              FROM qualitynode
              WHERE content ->> 'subchar' = %s AND pid = %s;
            '''
    cursor.execute(check_contribution, (node_name, pid,))
    nid = cursor.fetchone()

    # 品質ノードよりログを調べ前の達成度を得る
    achievement = 0.0
    if nid != None:   
      check_aim = '''
                  SELECT achievement
                  FROM log
                  WHERE nid = %s
                  ORDER BY lid DESC 
                  LIMIT 1;
              '''
      cursor.execute(check_aim, (nid[0],))
      result = cursor.fetchone()
      achievement = result[0] if result is not None else 0.0
        
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return round(achievement)

#########################################################
# 機能：  アーキテクチャノードより記述（手法）を得る
# 戻り値： description
#########################################################
def check_description(pid, node_name):
  try:
    connector = get_connector()       
    cursor = connector.cursor()

    check_aim = '''
                  SELECT content ->> 'description' as dvalue
                  FROM qualitynode
                  WHERE content ->> 'subchar' = %s AND pid = %s;
              '''
    cursor.execute(check_aim, (node_name, pid,))
    dvalue = cursor.fetchone()
    message = dvalue[0] if dvalue is not None else None

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
      cursor.close()
      connector.close()
      
  return message

#########################################################
# 機能：  supportテーブルから貢献度の獲得
# 戻り値： 親への貢献度
# Note：　親がない場合にも貢献度を設定している（要吟味）
#########################################################
def check_contribution(pid, node_name):
  try:
    connector = get_connector()   
    cursor = connector.cursor()

    # ノード名の品質ノードを獲得
    check_contribution = '''
              SELECT nid
              FROM qualitynode
              WHERE content ->> 'subchar' = %s AND pid = %s;
            '''
    cursor.execute(check_contribution, (node_name, pid,))
    nid = cursor.fetchone()

    # ノード名が存在すれば親への貢献度を獲得
    if nid:
      check_pid = '''
              SELECT contribution FROM support WHERE source = %s
            '''
      cursor.execute(check_pid, (nid[0],))
      existing_contribution = cursor.fetchone()
      message = existing_contribution[0]

    else:
      message = 0

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
      cursor.close()
      connector.close()

  return message

#########################################################
# 機能： 　品質ノード（品質活動）の目標値の獲得
# 戻り値： 品質活動の目標値 なければ　[0.70, 0.85]
#########################################################
def check_scope(pid, node_name):
  try:
    connector = get_connector()            
    cursor = connector.cursor()

    check_aim = '''
              SELECT content ->> 'tolerance' as tolerance_value
              FROM qualitynode
              WHERE content ->> 'subchar' = %s AND pid = %s;
            '''
    cursor.execute(check_aim, (node_name, pid,))
    svalue = cursor.fetchone()
    message = eval(svalue[0]) if svalue is not None else [0.70, 0.85]    

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return message

#########################################################
# 機能： 　projectテーブル全体の獲得
# 戻り値： 全プロジェクトについてのレコードのリスト
#########################################################
def read_table(request, pid=None):
  try:
    connector = get_connector()            
    cursor = connector.cursor()

    if pid == None:
      cursor.execute(request)
    else:
      cursor.execute(request, (pid,))
    data = cursor.fetchall()
    if data:
      message=data
    else:
      message='none'    

  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return message

#########################################################
# 機能： 木構造トップの品質ノードの情報出力
# 戻り値：　(content, achivement, contribution, nid) から
#         なるリストのリスト
# Note： 木構造トップの品質ノード，左ポートリンクによって判定(要吟味)
#########################################################
def getRoots(pid):
  try:
    connector = get_connector()             
    cursor = connector.cursor()

    check_aim = '''
              SELECT q.content, q.achievement, s.contribution, q.nid
              FROM qualitynode q
              JOIN support s ON q.nid = s.source
              WHERE s.destination = '0' AND q.pid = %s;
            '''
    cursor.execute(check_aim, (pid,))
    data = cursor.fetchall()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return data

#########################################################
# 機能：  品質ノードの達成度
# 入力：  nid 品質ノードID，sprint スプリント番号
# 戻り値：上記に対応する達成度
# Note： エラー処理がされていない
#########################################################
def achievement(nid, sprint):
  try:
    # PostgreSQLに接続
    connector = get_connector()
    cursor = connector.cursor()

    check_aim = '''
          SELECT achievement
          FROM log
          WHERE nid = %s AND sprint = %s;
        '''
    cursor.execute(check_aim, (nid, sprint,))
    result = cursor.fetchone()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return result

#########################################################
# 機能：プロジェクトの全ての品質ノードの取り出し
# 入力：　pid プロジェクトID
# 戻り値：　レコード(リスト)のリスト 
#########################################################
def get_nodes(pid):
  try:
    # PostgreSQLに接続
    connector = get_connector()    
    cursor = connector.cursor() 

    check_aim = '''
          SELECT *
          FROM qualitynode
          WHERE pid = %s ;
        '''
    cursor.execute(check_aim, (pid,))
    result = cursor.fetchall()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()

  return result
