DROP TABLE IF EXISTS `crawl_links`;
CREATE TABLE `crawl_links` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `type` varchar(32) DEFAULT NULL, -- 'link' or 'source'

  # request data
  `from_id` int(10) unsigned NOT NULL,
  `to_id` int(10) unsigned NOT NULL,
  `link_text` varchar(1024) DEFAULT NULL,
  `alt_text` varchar(1024) DEFAULT NULL,
  `rel` varchar(1024) DEFAULT NULL,

  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `from_id` (`from_id`),
  KEY `to_id` (`to_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `crawl_urls`;
CREATE TABLE `crawl_urls` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `level` tinyint(4) unsigned NOT NULL DEFAULT '0',
  `content_hash` varchar(64) DEFAULT NULL,

  # request data
  `address` varchar(2048) NOT NULL DEFAULT '',
  `domain` varchar(128) DEFAULT NULL,
  `path` varchar(2048) DEFAULT NULL,
  `external` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `status_code` int(10) unsigned DEFAULT NULL,
  `status` text,
  `body` longblob,
  `size` int(10) unsigned DEFAULT NULL,
  `address_length` int(10) unsigned NOT NULL,
  `encoding` varchar(16) DEFAULT NULL,
  `content_type` varchar(64) DEFAULT NULL,
  `response_time` float unsigned DEFAULT NULL,
  `redirect_uri` varchar(2048) DEFAULT NULL,

  # parse data
  `canonical` varchar(2048) DEFAULT NULL,
  `title_1` varchar(1024) DEFAULT NULL,
  `title_length_1` int(10) unsigned DEFAULT NULL,
  `title_occurences_1` int(10) unsigned DEFAULT NULL,
  `meta_description_1` varchar(2048) DEFAULT NULL,
  `meta_description_length_1` int(10) unsigned DEFAULT NULL,
  `meta_description_occurrences_1` int(10) unsigned DEFAULT NULL,
  `h1_1` varchar(2048) DEFAULT NULL,
  `h1_length_1` int(10) unsigned DEFAULT NULL,
  `h1_2` varchar(2048) DEFAULT NULL,
  `h1_length_2` int(10) unsigned DEFAULT NULL,
  `h1_count` int(10) unsigned DEFAULT NULL,
  `meta_robots` varchar(16) DEFAULT NULL,
  `rel_next` varchar(2048) DEFAULT NULL,
  `rel_prev` varchar(2048) DEFAULT NULL,

  # lint data
  `lint_critical` int(10) unsigned DEFAULT NULL,
  `lint_error` int(10) unsigned DEFAULT NULL,
  `lint_warn` int(10) unsigned DEFAULT NULL,
  `lint_info` int(10) unsigned DEFAULT NULL,
  `lint_results` text,

  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `crawl_save`;
CREATE TABLE `crawl_save` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `urls` longblob,
  `url_associations` longblob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;