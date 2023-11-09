import requests
import time
import json
import sqlite3

#https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames?_include_options=1&_items_per_page=100&_page_number=2&is_in_circulation=1

#https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames

page_number = 1

items = []

while True:
  url = "https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames?_include_options=1&_items_per_page=100&_page_number={}&is_in_circulation=1".format(page_number)

  r = requests.get(url)
  results = r.json()
  #items.extend(results['result']['items'])
 # import pdb; pdb.set_trace()
  if int(results['result']['paging']['page_number']) < int(results['result']['paging']['total_pages']):
    #import pdb; pdb.set_trace()
    page_number = int(results['result']['paging']['next_page_number'])
  else:
    break
  #print(page_number)
  # id int PRIMARY KEY, is_checked_out int, is_in_circulation int, publisher_name str, max_play_time int, min_play_time int, max_players int, min_players int, library_id str)


  try:
    sqliteConnection = sqlite3.connect('library.db',
                                        detect_types=sqlite3.PARSE_DECLTYPES |
                                                    sqlite3.PARSE_COLNAMES)
    cursor = sqliteConnection.cursor()
    print("Connected to SQLite")
    
    # delete existing. this is stupid, but I made a mistake in table design.

    query = """insert or ignore into games ('id', 'is_checked_out', 'is_in_circulation', 'name', 'publisher_name', 'max_play_time', 'min_play_time', 'max_players', 'min_players', 'library_id') values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

    for entry in results['result']['items']:
      id = entry['id']
      is_checked_out = entry['is_checked_out']
      is_in_circulation = entry['is_in_circulation']
      name = entry['name']
      publisher_name = entry['publisher_name']
      max_play_time = entry['max_play_time']
      min_play_time = entry['min_play_time']
      max_players = entry['max_players']
      min_players = entry['min_players']
      library_id = entry['library_id']

      data_tuple = (id, is_checked_out, is_in_circulation, name, publisher_name, max_play_time, min_play_time, max_players, min_players, library_id)

      cursor.execute(query, data_tuple)
      sqliteConnection.commit()
      print("Game added successfully \n")

    cursor.close()
  except sqlite3.Error as error:
    print("Error while working with SQLite", error)
  # if page_number == 3:
  #   break
  time.sleep(1)

json_formatted_str = json.dumps(items, indent=2)

print(json_formatted_str)
#print(items)

