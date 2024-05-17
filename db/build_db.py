from sqlitedict import SqliteDict as DB
import os

def build_notes(servers=None):
    notes_table = DB('db/db.sqlite', tablename='guilds', autocommit=True)
    if servers:
        for server in servers:
            if not notes_table[server.id]:
                notes_table[server.id] = {"prefix": "!", "notes": {}, "channels": []}
    notes_table.close()
            

if __name__ == "__main__":
    build_notes(servers=None)