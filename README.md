# IdeaBot
a discord bot for keeping track of our ideas and creating projects

## How to use
- You need MySQL running on your server
  - a database called `IdeaBot`
  - a table called `ideas`
- You need to edit the .env file to correspond to your environment


### table `ideas` in the `IdeaBot` database
```
+-------------+---------------+------+-----+---------+----------------+
| Field       | Type          | Null | Key | Default | Extra          |
+-------------+---------------+------+-----+---------+----------------+
| id          | int           | NO   | PRI | NULL    | auto_increment |
| name        | varchar(32)   | NO   |     | NULL    |                |
| subject     | varchar(32)   | YES  |     | NULL    |                |
| creator     | varchar(32)   | YES  |     | NULL    |                |
| difficulty  | int           | YES  |     | NULL    |                |
| description | varchar(255)  | YES  |     | NULL    |                |
| project     | decimal(32,0) | YES  |     | NULL    |                |
+-------------+---------------+------+-----+---------+----------------+
```

### `.env` file
```
DISCORD_TOKEN={YOUR DISCORD BOT TOKEN}
GUILD_ID={ID OF YOUR DISCORD SERVER}
CATEGORY_NAME={NAME OF THE CATEGORY FOR THE BOT}
SQL_USR={MYSQL USERNAME}
SQL_PWD={MYSQL PASSWORD}
```
