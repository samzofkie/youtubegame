from collections import OrderedDict

tables = OrderedDict()

tables['genres'] = (
        "CREATE TABLE `genres` ("
        "`id`       INT NOT NULL AUTO_INCREMENT,"
        "`name`     VARCHAR(64) NOT NULL UNIQUE,"
        "PRIMARY KEY (`id`) );"
        )

tables['videos'] = (
        "CREATE TABLE `videos` ("
        "`id`           INT         NOT NULL AUTO_INCREMENT,"
        "`uri`          VARCHAR(11) NOT NULL UNIQUE,"
        "`title`        VARCHAR(100),"
        "`views`        INT         UNSIGNED,"
        "`published`    DATE," 
        "`duration`     TIME,"
        "`genre_id`     INT,"
        "PRIMARY KEY (`id`),"
        "FOREIGN KEY (`genre_id`) REFERENCES genres(id) );"
        )

tables['interactions'] = (
        "CREATE TABLE `interactions` ("
        "`id`       INT NOT NULL AUTO_INCREMENT,"
        "`ip`		VARCHAR(16),"
		"`uri`    	VARCHAR(11) NOT NULL,"
        "`watch_time`   TIME,"
        "PRIMARY KEY (`id`),"
        "FOREIGN KEY (`uri`) REFERENCES videos(uri) );"
    )
