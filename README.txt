
Guard Server

1.  read profile get $SERVER_NAME

    $SERVER_NAME = "game_name" or "db_monitor"
    $$TEAM_NAME = "Team1" or "Team2" or "Team4" or "Team5" or "Team6" or "yunwei"

2.  do something

    game_name just do :

        1.  monitor program process

        2.  monitor program port

        3.  monitor program route

        4.  monitor supervisor program EXITED event

    db_monitor just do:

        1.  monitor db select、update（ Mysql | Redis | Mongodb ）

# 3.  make a /ishealth interface , you access it and you should get  "I Am Hortor Guard" that prove server is health




Usage：

    1.  Modify db.json or program.json

    2.  Modify guard.ini

    Monitor Program：

        guard.py: need use supervisor to run

        # Not installed the Supervisor, you can use the following command

            yum -y install supervisor && sh sync_supervisord.sh && supervisord -c /etc/supervisord.conf

        # Installed the Supervisor, you can use the following command

            sh sync_supervisord.sh && supervisorctl update

        # if you need update guard, you can use the following command

            git pull  && sh sync_supervisord.sh &&  supervisorctl restart guard

    Monitor db：

        guard.py: need use nohup to run

        # Run

            nohup python guard.py &



