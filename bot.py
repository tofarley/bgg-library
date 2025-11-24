# bot.py
import os
import random
import discord
import sqlite3
from discord.ext import commands
from dotenv import load_dotenv
import datetime
import urllib
import requests
import re
from unidecode import unidecode

MOCK_CHECKOUT = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL')
intents = discord.Intents.all()


def getUsers():
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        sqlite_delete_query = """delete from users where time <= date('now','-6 hour')"""
        print(sqlite_delete_query)
        cursor.execute(sqlite_delete_query)

        # get developer detail
        sqlite_select_query = """SELECT username, whereabouts, time from users"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()

        #import pdb; pdb.set_trace()
        for row in records:
        #     developer = row[0]
          joining_Date = row[2]
        #     print(developer, " joined on", joiningDate)
          print("joining date type is", type(joining_Date))

        cursor.close()
        return records

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    # finally:
    #     if (sqliteConnection):
    #         sqliteConnection.close()
    #         print("sqlite connection is closed")

def trackGame(id, username, gamename):
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        
        # delete existing. this is stupid, but I made a mistake in table design.

        sqlite_insert_with_param = """INSERT INTO 'games'
                          ('id', 'username', 'gamename') 
                          VALUES (?, ?, ?);"""
        
        data_tuple = (id, username, gamename)

        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqliteConnection.commit()
        print("Game added successfully \n")

        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    # finally:
    #     if sqliteConnection:
    #         sqliteConnection.close()
    #         print("sqlite connection is closed")

def checkinUser(name, whereabouts, joiningDate):
    try:
        sqliteConnection = sqlite3.connect('marco.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        
        # delete existing. this is stupid, but I made a mistake in table design.
        delete_existing_entry = """DELETE FROM users where username = (?);"""

        print(name)
        cursor.execute(delete_existing_entry, (name,))
        sqliteConnection.commit()
        # insert developer detail
        sqlite_insert_with_param = """INSERT INTO 'users'
                          ('username', 'whereabouts', 'time') 
                          VALUES (?, ?, ?);"""
        #location = "".join(ch for ch in whereabouts if ch.isalnum())
        location = whereabouts
        data_tuple = (name, location, joiningDate)
        #print(data_tuple)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqliteConnection.commit()
        print("Developer added successfully \n")

        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
    # finally:
    #     if sqliteConnection:
    #         sqliteConnection.close()
    #         print("sqlite connection is closed")


def chkList(lst):
    return len(set(lst)) != 1

def strip_parenthetical_content(name):
    """
    Remove parenthetical content (including the parentheses themselves) from a game name.
    This handles cases like "ANTS (English edition)" -> "ANTS"
    """
    # Remove content in parentheses: (content), [content], {content}
    # This regex matches parentheses, brackets, or braces and their contents
    cleaned = re.sub(r'[\(\[{][^\)\]}]*[\)\]}]', '', name)
    # Clean up any extra spaces left behind
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def filter_by_word_boundaries(items, search_term):
    """
    Filter results to only include games where the search term appears as a complete word.
    This prevents substring matches like "ants" matching "restaurants".
    
    For multi-word searches, checks that each word appears as a complete word in the game name.
    """
    if not search_term:
        return items
    
    # Normalize the search term for comparison
    normalized_search = unidecode(search_term.lower().strip())
    
    # Split the search term into individual words
    search_words = normalized_search.split()
    
    filtered_items = []
    for item in items:
        # Strip parenthetical content from the game name before comparison
        # This handles cases like "ANTS (English edition)" -> "ANTS"
        cleaned_name = strip_parenthetical_content(item['name'])
        # Normalize the game name for comparison
        normalized_name = unidecode(cleaned_name.lower())
        
        # Check if all words in the search term appear as complete words
        all_words_match = True
        for word in search_words:
            # Escape special regex characters in the word
            escaped_word = re.escape(word)
            # Create a regex pattern that matches the word as a whole word
            # \b matches word boundaries (between word and non-word characters)
            pattern = r'\b' + escaped_word + r'\b'
            if not re.search(pattern, normalized_name, re.IGNORECASE):
                all_words_match = False
                break
        
        if all_words_match:
            filtered_items.append(item)
    
    return filtered_items

def filter_by_word_start(items, search_term):
    """
    Fallback filter: if word boundary filtering returns no results, check if the search term
    appears at the start of any word in the game name. This helps with cases like searching
    for "ant" and finding "Ants".
    """
    if not search_term:
        return items
    
    normalized_search = unidecode(search_term.lower().strip())
    search_words = normalized_search.split()
    
    filtered_items = []
    for item in items:
        # Strip parenthetical content before comparison
        cleaned_name = strip_parenthetical_content(item['name'])
        normalized_name = unidecode(cleaned_name.lower())
        
        all_words_match = True
        for word in search_words:
            escaped_word = re.escape(word)
            # Match word that starts with the search term
            pattern = r'\b' + escaped_word
            if not re.search(pattern, normalized_name, re.IGNORECASE):
                all_words_match = False
                break
        
        if all_words_match:
            filtered_items.append(item)
    
    return filtered_items

bot = commands.Bot(command_prefix='!',intents=intents)

@bot.event
async def on_message(message):
    """
    Normalize command names to lowercase to make commands case-insensitive.
    This allows !IWANT, !CheckIn, !MARCO, etc. to work.
    """
    if message.content.startswith('!'):
        # Extract the command name (everything after ! until first space or end of string)
        parts = message.content[1:].split(maxsplit=1)
        command_name = parts[0]
        command_name_lower = command_name.lower()
        
        # Check if the lowercase version matches any registered command
        valid_commands = ['checkin', 'marco', 'iwant']
        
        if command_name_lower in valid_commands and command_name != command_name_lower:
            # Command name doesn't match case - normalize it
            # Reconstruct message content with lowercase command name
            if len(parts) > 1:
                normalized_content = '!' + command_name_lower + ' ' + parts[1]
            else:
                normalized_content = '!' + command_name_lower
            
            # Modify the message's internal _content attribute (discord.py stores content here)
            # Save original content
            original_content = None
            if hasattr(message, '_content'):
                original_content = message._content
                message._content = normalized_content
            elif hasattr(message, '__dict__'):
                # Try to access via __dict__ for older discord.py versions
                if '_content' in message.__dict__:
                    original_content = message.__dict__['_content']
                    message.__dict__['_content'] = normalized_content
                elif 'content' in message.__dict__:
                    original_content = message.__dict__['content']
                    message.__dict__['content'] = normalized_content
            
            # Process commands with normalized content
            try:
                await bot.process_commands(message)
            finally:
                # Restore original content
                if original_content is not None:
                    if hasattr(message, '_content'):
                        message._content = original_content
                    elif hasattr(message, '__dict__'):
                        if '_content' in message.__dict__:
                            message.__dict__['_content'] = original_content
                        elif 'content' in message.__dict__:
                            message.__dict__['content'] = original_content
            return
    
    # Process commands normally
    await bot.process_commands(message)

@bot.command(name='checkin', aliases=['CheckIn', 'CHECKIN', 'Checkin'], help='Checkin to an arbitrary location.')
async def checkin(ctx, *location):
    mystr = ' '.join(location)
    timestamp = datetime.datetime.now()
    checkinUser(ctx.author.display_name, mystr, timestamp)
    #import pdb; pdb.set_trace()

    msg = "{} checked in with: '{}' at {}".format(ctx.author.display_name, mystr, timestamp.strftime('%H:%M'))
    await ctx.send(msg)

@bot.command(name='marco', aliases=['Marco', 'MARCO'], help='See where everyone is hanging.')
async def marco(ctx):
    timestamp = datetime.datetime.now()
    users = getUsers()
    now = datetime.datetime.now()
    for user in users:
        timediff  = int(((now - user[2]).total_seconds()) / 60)
        time_unit = 'minutes'
        if timediff > 120:
            timediff = int(timediff / 60)
            time_unit = 'hours'
        msg = "{} last checked in with: {}, {} {} ago".format(user[0], user[1], timediff, time_unit)
        await ctx.send(msg)
    return

@bot.command(name='iwant', aliases=['IWant', 'IWANT', 'Iwant', 'iWant'], help='Checkin to an arbitrary location.')
async def iwant(ctx, *searchstring):
    if searchstring[0] == '~':
        searchstring = searchstring[1:]
        MOCK_CHECKOUT = True
    else:
        MOCK_CHECKOUT = False
        
    mystr = ' '.join(searchstring)


    ## remember to check on this later
    query = mystr
#    query = urllib.parse.quote_plus(mystr)
    print(query)

    r = requests.get('https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames?query=' + query)

    results = r.json()
    #import pdb; pdb.set_trace()
    
    # Debug: print how many results we got from the API
    original_items = results['result']['items'].copy()
    original_count = len(original_items)
    print(f"API returned {original_count} results for query: '{query}'")
    
    # Debug: print all API result names
    if original_count > 0:
        print("API result names:")
        for item in original_items[:10]:  # Print first 10
            print(f"  - {item['name']}")
        if original_count > 10:
            print(f"  ... and {original_count - 10} more")
    
    # First, check for exact matches (case-insensitive) - these should always be included
    # This handles games like "ANTS" when searching for "ants"
    # Strip parenthetical content for comparison (e.g., "ANTS (English edition)" -> "ANTS")
    normalized_search = unidecode(mystr.lower().strip())
    print(f"Normalized search term: '{normalized_search}'")
    exact_matches_in_api = []
    search_term_lower = normalized_search.lower()
    for item in original_items:
        cleaned_name = strip_parenthetical_content(item['name'])
        normalized_name = unidecode(cleaned_name.lower().strip())
        # Only print detailed info for items that might match (contain search term)
        if search_term_lower in normalized_name or search_term_lower in item['name'].lower():
            print(f"  Checking '{item['name']}' -> cleaned: '{cleaned_name}' -> normalized: '{normalized_name}'")
        if normalized_name == normalized_search:
            exact_matches_in_api.append(item)
            print(f"    ✓ Found exact match in API: {item['name']}")
    
    # Collect all exact matches first (from API and will add from DB)
    all_exact_matches = exact_matches_in_api.copy()
    
    # If we have exact matches, we'll prioritize them and filter out word-boundary matches
    # Otherwise, use word-boundary filtering
    if all_exact_matches:
        print(f"Found {len(all_exact_matches)} exact match(es) - will prioritize exact matches only")
        filtered_items = all_exact_matches.copy()
    else:
        # Filter results to only include games where the search term appears as a complete word
        # This prevents substring matches like "ants" matching "restaurants"
        filtered_items = filter_by_word_boundaries(original_items, mystr)
        print(f"Word boundary filter found {len(filtered_items)} matches:")
        for item in filtered_items:
            print(f"  - {item['name']}")
    
    # Debug: print how many results we have so far
    filtered_count = len(filtered_items)
    print(f"After initial filtering: {filtered_count} results")
    
    # Always check the local database as a supplement to API results
    # The API search may not return games where the search term is a complete word
    # (e.g., searching "ants" doesn't return "March of the Ants" or "ANTS")
    # We check the database even if we have API results to ensure we don't miss any games
    try:
        sqliteConnection = sqlite3.connect('library.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES |
                                                        sqlite3.PARSE_COLNAMES)
        cursor = sqliteConnection.cursor()
        
        # Get all games that contain the search term (simple substring match)
        # We'll filter with word boundaries afterwards
        normalized_search_db = unidecode(mystr.lower().strip())
        search_words = normalized_search_db.split()
        
        # Build query: games that contain all search words (as substrings)
        # Also check for exact match (case-insensitive) - this handles games like "ANTS"
        # Query: exact match OR (all words as substrings)
        exact_match_condition = "LOWER(TRIM(name)) = ?"
        exact_match_param = normalized_search_db
        
        # Build substring conditions for all words
        substring_conditions = []
        substring_params = []
        for word in search_words:
            substring_conditions.append("LOWER(name) LIKE ?")
            substring_params.append(f'%{word}%')
        
        # Combine: exact match OR (all words as substrings)
        if substring_conditions:
            where_clause = f"({exact_match_condition} OR ({' AND '.join(substring_conditions)}))"
            all_params = [exact_match_param] + substring_params
        else:
            where_clause = exact_match_condition
            all_params = [exact_match_param]
        
        query_sql = f"""SELECT DISTINCT name, id, is_checked_out, is_in_circulation, 
                      publisher_name, max_play_time, min_play_time, max_players, min_players, library_id
                      FROM games 
                      WHERE {where_clause}
                      ORDER BY name"""
        cursor.execute(query_sql, all_params)
        
        db_results = cursor.fetchall()
        cursor.close()
        
        print(f"Database query returned {len(db_results)} results")
        
        # Convert database results to the same format as API results and filter with word boundaries
        db_items = []
        exact_matches_in_db = []
        existing_item_ids = {item['id'] for item in filtered_items}  # Track IDs we already have
        
        # If we already have exact matches, only look for exact matches in the database
        # Otherwise, also include word-boundary matches
        prioritize_exact_only = len(all_exact_matches) > 0
        
        for row in db_results:
            temp_item = {
                'name': row[0],
                'id': row[1],
                'is_checked_out': row[2],
                'is_in_circulation': row[3],
                'publisher_name': row[4],
                'max_play_time': row[5],
                'min_play_time': row[6],
                'max_players': row[7],
                'min_players': row[8],
                'library_id': row[9]
            }
            # Skip if we already have this item from API results
            if temp_item['id'] in existing_item_ids:
                print(f"  Skipping '{temp_item['name']}' (ID {temp_item['id']}) - already in results")
                continue
                
            # Check for exact match first (strip parenthetical content)
            cleaned_name = strip_parenthetical_content(temp_item['name'])
            normalized_name = unidecode(cleaned_name.lower().strip())
            print(f"  Checking DB item '{temp_item['name']}' -> cleaned: '{cleaned_name}' -> normalized: '{normalized_name}'")
            if normalized_name == normalized_search_db:
                exact_matches_in_db.append(temp_item)
                print(f"    ✓ Found exact match in database: {temp_item['name']}")
            # Only apply word boundary filter if we're not prioritizing exact matches only
            elif not prioritize_exact_only and filter_by_word_boundaries([temp_item], mystr):
                db_items.append(temp_item)
                print(f"    ✓ Found word boundary match in database: {temp_item['name']}")
            else:
                if prioritize_exact_only:
                    print(f"    ✗ Skipping (exact matches only mode): {temp_item['name']}")
                else:
                    print(f"    ✗ No match for: {temp_item['name']}")
        
        # Always include exact matches from database
        for exact_match in exact_matches_in_db:
            db_items.append(exact_match)
            all_exact_matches.append(exact_match)
            print(f"Found exact match in database: {exact_match['name']}")
        
        # If we found ANY exact matches (from API or database), use ONLY exact matches
        if len(all_exact_matches) > 0:
            print(f"Found {len(all_exact_matches)} total exact match(es) - switching to exact-match-only mode")
            filtered_items = all_exact_matches.copy()
            filtered_count = len(filtered_items)
        # Otherwise, add database results (word-boundary matches) to filtered_items
        elif db_items:
            print(f"Found {len(db_items)} additional matching game(s) in local database")
            filtered_items.extend(db_items)
            filtered_count = len(filtered_items)
        else:
            print("No additional matches found in local database")
    except sqlite3.Error as error:
        print(f"Error querying local database: {error}")
    
    # If we still don't have an exact match, try querying the API with the exact search term
    # This handles cases where the game exists in the API but wasn't returned by the initial query
    # (e.g., "ANTS" might not be returned when searching "ants")
    existing_cleaned_names = [unidecode(strip_parenthetical_content(item['name']).lower().strip()) for item in filtered_items]
    if normalized_search not in existing_cleaned_names:
        print(f"Checking API for exact match '{mystr}'...")
        try:
            exact_r = requests.get('https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames?query=' + mystr)
            exact_results = exact_r.json()
            existing_ids = {item['id'] for item in filtered_items}
            
            for item in exact_results.get('result', {}).get('items', []):
                if item['id'] in existing_ids:
                    continue
                cleaned_name = strip_parenthetical_content(item['name'])
                normalized_name = unidecode(cleaned_name.lower().strip())
                if normalized_name == normalized_search:
                    filtered_items.append(item)
                    all_exact_matches.append(item)
                    filtered_count = len(filtered_items)
                    print(f"Found exact match in API: {item['name']}")
                    # If we now have exact matches and were using word-boundary matches, switch to exact-only
                    if len(all_exact_matches) == 1 and filtered_count > 1:
                        print("Switching to exact-match-only mode")
                        filtered_items = all_exact_matches.copy()
                        filtered_count = len(filtered_items)
                    break
        except Exception as e:
            print(f"Error querying API for exact match: {e}")
    
    # If filtering removed all results, try fallback strategies
    if original_count > 0 and filtered_count == 0:
        print("Warning: All results were filtered out. Trying fallback strategies...")
        normalized_search = unidecode(mystr.lower().strip())
        
        # First, check for exact matches (case-insensitive)
        # Strip parenthetical content for comparison
        exact_matches = []
        for item in original_items:
            cleaned_name = strip_parenthetical_content(item['name'])
            normalized_name = unidecode(cleaned_name.lower().strip())
            if normalized_name == normalized_search:
                exact_matches.append(item)
                print(f"  Found exact match: {item['name']}")
        
        if exact_matches:
            filtered_items = exact_matches
            filtered_count = len(filtered_items)
            print(f"Using {filtered_count} exact match(es)")
        else:
            # Second, check if search term appears at the start of any word
            # This helps with cases like searching "ant" and finding "Ants"
            # Only do this for single-word searches to avoid complexity
            if len(normalized_search.split()) == 1:
                word_start_matches = []
                search_word = normalized_search
                for item in original_items:
                    # Strip parenthetical content before comparison
                    cleaned_name = strip_parenthetical_content(item['name'])
                    normalized_name = unidecode(cleaned_name.lower())
                    # Split the game name into words and check if any word starts with the search term
                    words_in_name = re.findall(r'\b\w+', normalized_name)
                    for name_word in words_in_name:
                        if name_word.startswith(search_word):
                            word_start_matches.append(item)
                            break
                
                if word_start_matches:
                    filtered_items = word_start_matches
                    filtered_count = len(filtered_items)
                    print(f"Using {filtered_count} word-start match(es) (search term starts a word)")
                else:
                    print("No word-start matches found. First few original results:")
                    for item in original_items[:5]:
                        print(f"  - {item['name']}")
            else:
                print("Multi-word search with no matches. First few original results:")
                for item in original_items[:5]:
                    print(f"  - {item['name']}")
    
    # Final safeguard: if we have exact matches, ensure filtered_items only contains exact matches
    if len(all_exact_matches) > 0:
        exact_match_ids = {item['id'] for item in all_exact_matches}
        filtered_items = [item for item in filtered_items if item['id'] in exact_match_ids]
        print(f"Final safeguard: filtered to {len(filtered_items)} exact match(es) only")
    
    results['result']['items'] = filtered_items
    
    print(f"\n=== FINAL RESULTS: {len(filtered_items)} game(s) ===")
    for item in filtered_items:
        print(f"  - {item['name']} (ID: {item['id']})")
    
    print(f"Total exact matches found: {len(all_exact_matches)}")
    if len(all_exact_matches) > 0:
        print("Exact matches:")
        for item in all_exact_matches:
            print(f"  - {item['name']}")

    if len(results['result']['items']) > 1:
        # If we're in exact-match-only mode, all items are already exact matches
        # so we don't need to re-filter. Just check if they're all the same game.
        if len(all_exact_matches) > 0:
            # All items are exact matches - check if they're all the same game (by cleaned name)
            cleaned_names = [strip_parenthetical_content(item['name']) for item in results['result']['items']]
            normalized_cleaned_names = [unidecode(name.lower().strip()) for name in cleaned_names]
            if len(set(normalized_cleaned_names)) == 1:
                # All exact matches are the same game - use them as-is
                lst = [item['name'] for item in results['result']['items']]
            else:
                # Multiple different exact matches - this shouldn't happen, but handle it
                lst = [item['name'] for item in results['result']['items']]
        else:
            # Not in exact-match-only mode - use original logic but strip parenthetical content
            lst = []
            perfect_match = []
            perfect_lst = []
            final_list = []
            regular_match = []
            regular_lst = []
            normalized_search_check = unidecode(mystr.lower().strip())
            for entry in results['result']['items']:
                # Strip parenthetical content for comparison
                cleaned_entry_name = strip_parenthetical_content(entry['name'])
                normalized_entry_name = unidecode(cleaned_entry_name.lower().strip())
                if normalized_entry_name == normalized_search_check:
                    # we found the right game.
                    print(entry['name'] + ' is ' + mystr)
                    perfect_match.append(entry)
                    perfect_lst.append(entry['name'])
                else:
                    regular_match.append(entry)
                    regular_lst.append(entry['name'])
            #print(lst)
            if len(perfect_match) > 0:
                results['result']['items'] = perfect_match
                lst = perfect_lst
            else:
                results['result']['items'] = regular_match
                lst = regular_lst
        
        if chkList(lst):
            msg = "Too many results. Be more specific."
            await ctx.send(msg)
#            print(msg)
            # Show only the first 6 results
            items_to_show = results['result']['items'][:6]
            for result in items_to_show:
                msg = result['name']
#                print(msg)
                await ctx.send(msg)
            # If there are more than 6 results, indicate the list has been truncated
            if len(results['result']['items']) > 6:
                msg = f"... (list truncated, {len(results['result']['items']) - 6} more result(s) not shown)"
                await ctx.send(msg)
        else:
            #import pdb; pdb.set_trace()
            copies_available = 0
            copies_checkedout = []
            # Get the game name from the first result (all results should be the same game at this point)
            game_name = results['result']['items'][0]['name']
            for result in results['result']['items']:
                if MOCK_CHECKOUT == True:
                    result['is_checked_out'] = 1
                if result['is_checked_out'] == 0:
                    copies_available += 1
                else:
                    # We want to track the copies checked out...
                    copies_checkedout.append([result['id'], ctx.author.id, result['name']])
            
            # Check availability after counting all copies
            if copies_available == 0:
                msg = f"All copies of '{game_name}' are checked out. I will notify you when one becomes available."
                for entry in copies_checkedout:
                    trackGame(entry[0], entry[1], entry[2])
            else:
                msg = f"Found {copies_available} copies of '{game_name}' are currently available for checkout."
      
            await ctx.send(msg)
#            print(msg)
    elif len(results['result']['items']) == 1:
        if MOCK_CHECKOUT == True:
          results['result']['items'][0]['is_checked_out'] = 1
        msg = "Found the game you were looking for!"
        game_name = results['result']['items'][0]['name']
        if results['result']['items'][0]['is_checked_out'] == 1:
            msg = f"Oh no! The game '{game_name}' is checked out! I will notify you when it is available!"
            trackGame(results['result']['items'][0]['id'], ctx.author.id, game_name)
        else:
            msg = f"The game '{game_name}' is in the library. Go Go Go Go!"
        await ctx.send(msg)
#        print(msg)
    else:
        msg = "Nothing found"
        await ctx.send(msg)
#        print(msg)

    

bot.run(TOKEN)
