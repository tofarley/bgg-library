# Changelog - bot.py Updates

## Summary of Changes (bot.py vs bot.py.bak)

### 1. **Fixed Marco Database Cleanup** 🧹
   - **Fixed**: Users are now properly removed from `!marco` after 6 hours
   - **Problem**: Old check-ins were persisting in the database even after 6+ hours
   - **Root Causes**:
     - SQL query was using `date()` function instead of `datetime()` for timestamp comparison
     - Missing `commit()` statement meant deletions weren't being saved to the database
   - **Solution**:
     - Changed `date('now','-6 hour')` to `datetime('now','-6 hour')` for proper timestamp comparison
     - Added `sqliteConnection.commit()` after deletion to persist changes
   - **Behavior**: When you run `!marco`, any check-ins older than 6 hours are automatically cleaned up
   - **Backup**: Created `bot.py.marco-db` backup before changes

### 2. **Case-Insensitive Commands** 🔤
   - **Added**: Case-insensitive command recognition for all bot commands
   - **Purpose**: Commands now work regardless of capitalization (e.g., `!IWANT`, `!CheckIn`, `!MARCO`)
   - **Implementation**: 
     - Added `on_message` event handler that normalizes command names to lowercase before processing
     - Added aliases for common case variations as a backup mechanism
     - Commands affected: `!iwant`, `!checkin`, `!marco`
   - **Behavior**: 
     - All case variations are normalized to lowercase before command processing
     - Original message content is preserved after command execution
     - Works with all case combinations (e.g., `!ChEcKiN`, `!IWANT`, `!MaRcO`)
   - **Technical Details**:
     - Modifies message's internal `_content` attribute temporarily during processing
     - Supports multiple discord.py versions via fallback mechanisms
     - No library upgrades required - works with existing discord.py installation
   - **Backup Files**: Created `.bak.2025` backups before changes

### 2. **Word-Boundary Filtering** ✨
   - **Added**: `filter_by_word_boundaries()` function to prevent substring matches
   - **Purpose**: Searching for "ants" no longer returns games like "restaurants" or "merchants"
   - **Implementation**: Uses regex word boundaries (`\b`) to ensure search terms match complete words only

### 3. **Parenthetical Content Handling** 📝
   - **Added**: `strip_parenthetical_content()` function
   - **Purpose**: Handles games with parenthetical content like "ANTS (English edition)"
   - **Behavior**: Strips content in `()`, `[]`, and `{}` brackets before comparison
   - **Impact**: Searching for "ants" now correctly finds "ANTS (English edition)" as an exact match

### 4. **Exact Match Prioritization** 🎯
   - **Added**: Exact-match-only mode when exact matches are found
   - **Behavior**: 
     - If an exact match exists (after stripping parentheticals), ONLY exact matches are returned
     - Word-boundary matches are excluded when exact matches are present
   - **Example**: Searching "ants" returns only "ANTS (English edition)", not "March of the Ants"

### 5. **Database Integration** 🗄️
   - **Added**: Comprehensive database search as supplement to API results
   - **Features**:
     - Always checks local `library.db` in addition to API
     - Finds games the API might miss or under-prioritize
     - Respects exact-match-only mode when applicable
   - **Query Logic**: Searches for exact matches OR word-boundary matches based on mode

### 6. **Enhanced User Messages** 💬
   - **Improved**: All success messages now include the game name
   - **Changes**:
     - Single match: `"The game 'ANTS (English edition)' is in the library. Go Go Go Go!"`
     - Multiple copies: `"Found 3 copies of 'ANTS (English edition)' are currently available for checkout."`
     - Checked out: `"All copies of 'ANTS (English edition)' are checked out. I will notify you when one becomes available."`

### 7. **Result Limiting** 📊
   - **Added**: Limit "too many results" to first 6 items
   - **Behavior**: Shows first 6 results + truncation message if more exist
   - **Message**: `"... (list truncated, X more result(s) not shown)"`

### 8. **Debug Logging** 🔍
   - **Added**: Comprehensive debug output throughout the search process
   - **Includes**:
     - API result counts and names
     - Exact match detection
     - Word-boundary filtering results
     - Database query results
     - Final result summary

### 9. **Code Improvements** 🛠️
   - **Added**: `import re` for regex support
   - **Fixed**: Logic bug where availability check was inside loop (moved outside)
   - **Improved**: ID-based comparison instead of object identity for exact matches
   - **Enhanced**: Post-processing logic respects exact-match-only mode

## Technical Details

### New Functions
- `on_message(message)` event handler: Normalizes command names to lowercase for case-insensitive command recognition
- `strip_parenthetical_content(name)`: Removes parenthetical content from game names
- `filter_by_word_boundaries(items, search_term)`: Filters items to only include word-boundary matches
- `filter_by_word_start(items, search_term)`: Fallback filter (currently unused but available)

### Modified Flow
1. Fetch results from API
2. Check for exact matches (with parenthetical stripping)
3. Apply word-boundary filtering OR use exact matches only
4. Query local database (always, as supplement)
5. If exact matches found, switch to exact-match-only mode
6. Final safeguard: ensure filtered_items only contains exact matches if in exact-match-only mode
7. Post-process results with improved messaging

## Breaking Changes
None - all changes are backward compatible and improve functionality.

## Files Modified
- `bot.py`: Main bot file with all improvements
- `bot.py.bak`: Original backup (unchanged)
- `bot.py.bak.2025`: Backup created before case-insensitive command changes
- `runner.py.bak.2025`: Backup created before case-insensitive command changes
