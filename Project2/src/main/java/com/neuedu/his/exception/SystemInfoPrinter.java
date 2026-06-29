package com.neuedu.his.exception;

import org.springframework.core.io.support.SpringFactoriesLoader;

import java.io.File;
import java.lang.management.*;
import java.net.URL;
import java.net.URLClassLoader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public class SystemInfoPrinter {

    public static void main(String[] args) {
        printAllInfo();
    }

    public static void printAllInfo() {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        System.out.println("\n" + "=".repeat(80));
        System.out.println("🔍 智慧云脑诊疗平台 - 完整环境信息报告");
        System.out.println("生成时间: " + timestamp);
        System.out.println("=".repeat(80));

        printSystemInfo();
        printJavaInfo();
        printJvmInfo();
        printClasspathInfo();
        printMavenDependenciesInfo();
        printProjectModulesInfo();
        printEnvironmentVariables();

        System.out.println("\n" + "=".repeat(80));
        System.out.println("✅ 环境信息采集完成！请将以上内容复制发给队友");
        System.out.println("=".repeat(80) + "\n");

        System.exit(0);
    }

    private static void printSystemInfo() {
        printHeader("📌 【系统信息】");
        System.out.printf("  操作系统: %s %s%n",
                System.getProperty("os.name"),
                System.getProperty("os.version"));
        System.out.printf("  系统架构: %s%n", System.getProperty("os.arch"));
        System.out.printf("  用户名称: %s%n", System.getProperty("user.name"));
        System.out.printf("  用户目录: %s%n", System.getProperty("user.home"));
        System.out.printf("  工作目录: %s%n", System.getProperty("user.dir"));
        System.out.printf("  文件编码: %s%n", System.getProperty("file.encoding"));
        System.out.printf("  文件分隔符: %s%n", File.separator);
        System.out.printf("  路径分隔符: %s%n", File.pathSeparator);
        System.out.printf("  行分隔符: %s%n", System.lineSeparator().replace("\n", "\\n").replace("\r", "\\r"));

        OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
        System.out.printf("  系统负载: %.2f%n", osBean.getSystemLoadAverage());
        System.out.printf("  可用处理器: %d%n", osBean.getAvailableProcessors());
        System.out.println();
    }

    private static void printJavaInfo() {
        printHeader("📌 【Java 环境】");
        System.out.printf("  JDK版本: %s%n", System.getProperty("java.version"));
        System.out.printf("  JDK厂商: %s%n", System.getProperty("java.vendor"));
        System.out.printf("  JDK版本号: %s%n", System.getProperty("java.vm.version"));
        System.out.printf("  JVM名称: %s%n", System.getProperty("java.vm.name"));
        System.out.printf("  JVM厂商: %s%n", System.getProperty("java.vm.vendor"));
        System.out.printf("  JRE路径: %s%n", System.getProperty("java.home"));
        System.out.printf("  Java规范版本: %s%n", System.getProperty("java.specification.version"));
        System.out.printf("  Java类版本: %s%n", System.getProperty("java.class.version"));
        System.out.printf("  JIT编译器: %s%n", System.getProperty("java.compiler", "未知"));
        System.out.println();
    }

    private static void printJvmInfo() {
        printHeader("📌 【JVM 内存与参数】");

        Runtime runtime = Runtime.getRuntime();
        System.out.printf("  最大内存: %.2f MB%n", runtime.maxMemory() / 1024.0 / 1024.0);
        System.out.printf("  总内存: %.2f MB%n", runtime.totalMemory() / 1024.0 / 1024.0);
        System.out.printf("  空闲内存: %.2f MB%n", runtime.freeMemory() / 1024.0 / 1024.0);
        System.out.printf("  已用内存: %.2f MB%n", (runtime.totalMemory() - runtime.freeMemory()) / 1024.0 / 1024.0);

        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        System.out.printf("  堆内存使用: %.2f MB%n", memoryBean.getHeapMemoryUsage().getUsed() / 1024.0 / 1024.0);
        System.out.printf("  非堆内存使用: %.2f MB%n", memoryBean.getNonHeapMemoryUsage().getUsed() / 1024.0 / 1024.0);

        RuntimeMXBean runtimeBean = ManagementFactory.getRuntimeMXBean();
        System.out.println("\n  JVM启动参数:");
        for (String arg : runtimeBean.getInputArguments()) {
            System.out.printf("    %s%n", arg);
        }
        System.out.println();
    }

    private static void printClasspathInfo() {
        printHeader("📌 【Classpath 信息】");

        ClassLoader cl = ClassLoader.getSystemClassLoader();
        if (cl instanceof URLClassLoader) {
            URLClassLoader ucl = (URLClassLoader) cl;
            URL[] urls = ucl.getURLs();
            System.out.printf("  共有 %d 个classpath条目%n", urls.length);
            System.out.println("  主要依赖路径:");
            int count = 0;
            for (URL url : urls) {
                if (count++ < 20) {  // 只显示前20个
                    String path = url.getPath();
                    if (path.contains("repository")) {
                        // 提取jar名称
                        String jarName = path.substring(path.lastIndexOf(File.separator) + 1);
                        System.out.printf("    %s%n", jarName);
                    }
                }
            }
            if (urls.length > 20) {
                System.out.printf("    ... 还有 %d 个%n", urls.length - 20);
            }
        }
        System.out.println();
    }

    private static void printMavenDependenciesInfo() {
        printHeader("📌 【Maven 核心依赖版本】");

        Map<String, String> deps = new LinkedHashMap<>();
        deps.put("Spring Boot", "org.springframework.boot.SpringApplication");
        deps.put("MyBatis", "org.mybatis.spring.SqlSessionFactoryBean");
        deps.put("MyBatis-Spring", "org.mybatis.spring.SqlSessionTemplate");
        deps.put("PageHelper", "com.github.pagehelper.PageHelper");
        deps.put("PostgreSQL JDBC", "org.postgresql.Driver");
        deps.put("Lombok", "lombok.core.Main");
        deps.put("JJWT", "io.jsonwebtoken.Jwts");
        deps.put("SpringDoc", "org.springdoc.core.models.OpenAPI");
        deps.put("Jackson", "com.fasterxml.jackson.core.JsonFactory");
        deps.put("Hibernate Validator", "org.hibernate.validator.HibernateValidator");
        deps.put("Logback", "ch.qos.logback.core.CoreConstants");
        deps.put("Tomcat Embed", "org.apache.catalina.startup.Tomcat");

        for (Map.Entry<String, String> entry : deps.entrySet()) {
            try {
                Class.forName(entry.getValue());
                System.out.printf("  ✅ %s: 已加载%n", entry.getKey());
            } catch (ClassNotFoundException e) {
                System.out.printf("  ❌ %s: 未找到%n", entry.getKey());
            } catch (NoClassDefFoundError e) {
                System.out.printf("  ⚠️ %s: 部分加载%n", entry.getKey());
            }
        }

        // 尝试获取Spring Boot版本
        try {
            Properties props = new Properties();
            props.load(SpringFactoriesLoader.class.getResourceAsStream("/META-INF/spring-boot-starter-parent.properties"));
            String version = props.getProperty("parent.version");
            if (version != null) {
                System.out.printf("  📌 Spring Boot 父版本: %s%n", version);
            }
        } catch (Exception e) {
            // 忽略
        }
        System.out.println();
    }

    private static void printProjectModulesInfo() {
        printHeader("📌 【项目模块结构】");
        System.out.println("  hismodules (父模块)");
        System.out.println("  ├── his-common (公共模块)");
        System.out.println("  ├── his-outpatient (门诊模块)");
        System.out.println("  ├── his-drugstore (药房模块)");
        System.out.println("  └── his-ai (AI模块)");

        // 检查当前模块
        String currentDir = System.getProperty("user.dir");
        System.out.printf("\n  当前工作目录: %s%n", currentDir);

        // 检查是否在多模块环境中
        File pomFile = new File(currentDir, "pom.xml");
        if (pomFile.exists()) {
            System.out.println("  ✅ 检测到 Maven 项目 (pom.xml 存在)");
        }

        File parentPom = new File(currentDir, "../pom.xml");
        if (parentPom.exists()) {
            System.out.println("  📌 检测到多模块项目结构 (父pom存在)");
        }
        System.out.println();
    }

    private static void printEnvironmentVariables() {
        printHeader("📌 【环境变量 (开发相关)】");

        Map<String, String> env = System.getenv();
        String[] keys = {
                "JAVA_HOME", "MAVEN_HOME", "M2_HOME", "GRADLE_HOME",
                "PATH", "CLASS_PATH", "CLASSPATH",
                "DB_URL", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USERNAME",
                "JWT_SECRET", "ACTUATOR_ENABLED"
        };

        for (String key : keys) {
            String value = env.get(key);
            if (value != null && !value.isEmpty()) {
                if (key.equals("PATH") && value.length() > 100) {
                    value = value.substring(0, 100) + "...";
                }
                System.out.printf("  %s = %s%n", key, value);
            } else {
                System.out.printf("  %s = (未设置)%n", key);
            }
        }

        // 检查Maven是否在PATH中
        String path = env.get("PATH");
        if (path != null && path.toLowerCase().contains("maven")) {
            System.out.println("\n  ✅ Maven 已在 PATH 中");
        } else if (path != null && path.toLowerCase().contains("apache-maven")) {
            System.out.println("\n  ✅ Maven 已在 PATH 中");
        } else {
            System.out.println("\n  ⚠️ Maven 可能不在 PATH 中");
        }
        System.out.println();
    }

    private static void printHeader(String title) {
        System.out.println("\n" + title);
        System.out.println("-".repeat(60));
    }
}