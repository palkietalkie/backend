-- "display_name" misled: the column is never rendered as a display. It's read into the LLM prompt (so the tutor addresses the user by it), used for KG self-matching, and is the user-editable name field. Renamed to preferred_name — unambiguous (not a username or legal name): the name the user wants to be addressed by. Pairs with the existing name_pronunciation.

ALTER TABLE users RENAME COLUMN display_name TO preferred_name;
