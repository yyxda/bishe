/*
 Navicat Premium Dump SQL

 Source Server         : Hierarch
 Source Server Type    : MySQL
 Source Server Version : 80044 (8.0.44-0ubuntu0.22.04.2)
 Source Host           : 192.168.0.21:3306
 Source Schema         : Argus

 Target Server Type    : MySQL
 Target Server Version : 80044 (8.0.44-0ubuntu0.22.04.2)
 File Encoding         : 65001

 Date: 07/01/2026 16:52:58
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for email_accounts
-- ----------------------------
DROP TABLE IF EXISTS `email_accounts`;
CREATE TABLE `email_accounts`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `email_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱地址',
  `email_type` enum('DEFAULT','QQ','NETEASE','CUSTOM') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱类型',
  `imap_host` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'IMAP服务器',
  `imap_port` bigint NOT NULL COMMENT 'IMAP端口',
  `smtp_host` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'SMTP服务器',
  `smtp_port` bigint NOT NULL COMMENT 'SMTP端口',
  `use_ssl` tinyint(1) NOT NULL COMMENT '是否使用SSL',
  `auth_user` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '认证用户名',
  `auth_password_encrypted` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '加密后的密码',
  `is_active` tinyint(1) NOT NULL COMMENT '是否启用',
  `last_sync_at` datetime NULL DEFAULT NULL COMMENT '最后同步时间',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_email_accounts_user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `email_accounts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for email_bodies
-- ----------------------------
DROP TABLE IF EXISTS `email_bodies`;
CREATE TABLE `email_bodies`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `message_id` bigint NOT NULL COMMENT '邮件元数据ID',
  `content_text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `content_html` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_email_bodies_message_id`(`message_id` ASC) USING BTREE,
  CONSTRAINT `email_bodies_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `email_messages` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for email_messages
-- ----------------------------
DROP TABLE IF EXISTS `email_messages`;
CREATE TABLE `email_messages`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `email_account_id` bigint NOT NULL COMMENT '邮箱账户ID',
  `message_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮件唯一标识',
  `subject` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮件主题',
  `sender_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发件人姓名',
  `sender_address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发件人邮箱',
  `snippet` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '邮件摘要',
  `received_at` datetime NULL DEFAULT NULL COMMENT '接收时间',
  `size` int NULL DEFAULT NULL COMMENT '邮件大小',
  `phishing_level` enum('NORMAL','SUSPICIOUS','HIGH_RISK') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '钓鱼危险等级',
  `phishing_score` float NOT NULL COMMENT '钓鱼评分',
  `phishing_reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '钓鱼判定原因',
  `phishing_status` enum('PENDING','COMPLETED','FAILED') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'COMPLETED' COMMENT '钓鱼检测状态',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_email_account_message_id`(`email_account_id` ASC, `message_id` ASC) USING BTREE,
  INDEX `ix_email_messages_message_id`(`message_id` ASC) USING BTREE,
  INDEX `ix_email_account_received_at`(`email_account_id` ASC, `received_at` ASC) USING BTREE,
  INDEX `ix_email_messages_email_account_id`(`email_account_id` ASC) USING BTREE,
  INDEX `ix_email_messages_received_at`(`received_at` ASC) USING BTREE,
  CONSTRAINT `email_messages_ibfk_1` FOREIGN KEY (`email_account_id`) REFERENCES `email_accounts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for email_recipients
-- ----------------------------
DROP TABLE IF EXISTS `email_recipients`;
CREATE TABLE `email_recipients`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `message_id` bigint NOT NULL COMMENT '邮件元数据ID',
  `recipient_type` enum('TO','CC','BCC','REPLY_TO') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '收件人类型',
  `display_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '显示名称',
  `email_address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱地址',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_email_recipients_message_id`(`message_id` ASC) USING BTREE,
  CONSTRAINT `email_recipients_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `email_messages` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for mailbox_messages
-- ----------------------------
DROP TABLE IF EXISTS `mailbox_messages`;
CREATE TABLE `mailbox_messages`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `mailbox_id` bigint NOT NULL COMMENT '邮箱文件夹ID',
  `message_id` bigint NOT NULL COMMENT '邮件元数据ID',
  `uid` bigint NOT NULL COMMENT 'IMAP UID',
  `flags` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'IMAP标志位',
  `is_read` tinyint(1) NOT NULL COMMENT '是否已读',
  `is_flagged` tinyint(1) NOT NULL COMMENT '是否标星',
  `is_answered` tinyint(1) NOT NULL COMMENT '是否已回复',
  `is_deleted` tinyint(1) NOT NULL COMMENT '是否删除',
  `is_draft` tinyint(1) NOT NULL COMMENT '是否草稿',
  `internal_date` datetime NULL DEFAULT NULL COMMENT '内部日期',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_mailbox_uid`(`mailbox_id` ASC, `uid` ASC) USING BTREE,
  INDEX `ix_mailbox_messages_mailbox_id`(`mailbox_id` ASC) USING BTREE,
  INDEX `ix_mailbox_internal_date`(`mailbox_id` ASC, `internal_date` ASC) USING BTREE,
  INDEX `ix_mailbox_messages_message_id`(`message_id` ASC) USING BTREE,
  CONSTRAINT `mailbox_messages_ibfk_1` FOREIGN KEY (`mailbox_id`) REFERENCES `mailboxes` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `mailbox_messages_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `email_messages` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for mailboxes
-- ----------------------------
DROP TABLE IF EXISTS `mailboxes`;
CREATE TABLE `mailboxes`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `email_account_id` bigint NOT NULL COMMENT '邮箱账户ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件夹名称',
  `delimiter` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '层级分隔符',
  `attributes` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '文件夹属性',
  `uid_validity` bigint NULL DEFAULT NULL COMMENT 'UID有效期',
  `last_uid` bigint NOT NULL COMMENT '最后同步UID',
  `last_sync_at` datetime NULL DEFAULT NULL COMMENT '最后同步时间',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_mailbox_account_name`(`email_account_id` ASC, `name` ASC) USING BTREE,
  INDEX `ix_mailboxes_email_account_id`(`email_account_id` ASC) USING BTREE,
  CONSTRAINT `mailboxes_ibfk_1` FOREIGN KEY (`email_account_id`) REFERENCES `email_accounts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `student_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学号',
  `password_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `display_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名称',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT '用户角色',
  `created_at` datetime NULL DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT (now()) COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_users_student_id`(`student_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- 初始化默认超级管理员账号（首次执行时写入）
INSERT INTO `users` (`student_id`, `password_hash`, `display_name`, `is_active`, `role`, `created_at`, `updated_at`)
SELECT 'Administrator',
       'e7d3e769f3f593dadcb8634cc5b09fc90dd3a61c4a06a79cb0923662fe6fae6b',
       'Administrator',
       1,
       'super_admin',
       now(),
       now()
WHERE NOT EXISTS (
  SELECT 1 FROM `users` WHERE `student_id` = 'Administrator'
);

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- 2026-01-08: 管理员功能扩展
-- ----------------------------
-- users表新增字段: is_active TINYINT(1) DEFAULT 1, role VARCHAR(20) DEFAULT 'user'

-- ----------------------------
-- 2026-03-31: 邮箱登录功能扩展
-- ----------------------------
ALTER TABLE `users` 
ADD COLUMN `email` VARCHAR(100) NULL COMMENT '邮箱地址' AFTER `updated_at`,
ADD COLUMN `email_type` VARCHAR(20) NULL COMMENT '邮箱类型: qq, 163, netease等' AFTER `email`,
ADD COLUMN `auth_code` VARCHAR(100) NULL COMMENT '授权码' AFTER `email_type`,
ADD INDEX `ix_users_email`(`email` ASC);
-- 新增表: url_whitelist (URL白名单规则表)
--   字段: id, rule_type, rule_value, description, is_active, created_at, updated_at
--   唯一索引: uq_rule (rule_type, rule_value)

-- ----------------------------
-- Table structure for url_whitelist
-- ----------------------------
DROP TABLE IF EXISTS `url_whitelist`;
CREATE TABLE `url_whitelist`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NULL COMMENT '用户ID（NULL表示全局白名单）',
  `rule_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则类型：DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD',
  `rule_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则值',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '规则描述',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_rule`(`rule_type` ASC, `rule_value` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'URL白名单规则表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for sender_whitelist
-- ----------------------------
DROP TABLE IF EXISTS `sender_whitelist`;
CREATE TABLE `sender_whitelist`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NULL COMMENT '用户ID（NULL表示全局白名单）',
  `rule_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则类型：EMAIL/DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD',
  `rule_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则值',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '规则描述',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_sender_rule`(`rule_type` ASC, `rule_value` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '发件人白名单规则表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for system_settings
-- ----------------------------
DROP TABLE IF EXISTS `system_settings`;
CREATE TABLE `system_settings`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `enable_long_url_detection` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用长链接检测',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统设置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- 2026-04-03: 批量更新PENDING状态邮件为COMPLETED
-- ----------------------------
-- 说明：将所有处于PENDING（检测中）状态的邮件批量更新为COMPLETED（已完成）
-- 原因：邮件同步时设置为PENDING状态，但后台检测任务未正常启动，导致邮件一直显示"正在检测"
-- 解决方案：直接将状态更新为COMPLETED，避免邮件一直显示"正在检测"
UPDATE `email_messages` 
SET `phishing_status` = 'COMPLETED' 
WHERE `phishing_status` = 'PENDING';

-- ----------------------------
-- 2026-04-15: 为白名单表添加 user_id 字段
-- ----------------------------
-- 说明：为 url_whitelist 和 sender_whitelist 表添加 user_id 字段，支持用户级别的白名单
-- 原因：需要支持每个用户有自己的白名单，而不是所有用户共享全局白名单
-- 解决方案：添加 user_id 字段，NULL 表示全局白名单，非 NULL 表示用户白名单
ALTER TABLE `url_whitelist` ADD COLUMN `user_id` bigint NULL COMMENT '用户ID（NULL表示全局白名单）' AFTER `id`;
ALTER TABLE `sender_whitelist` ADD COLUMN `user_id` bigint NULL COMMENT '用户ID（NULL表示全局白名单）' AFTER `id`;