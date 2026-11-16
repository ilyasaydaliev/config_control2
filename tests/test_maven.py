"""Тесты разбора pom.xml: версии, scope, dependencyManagement."""

import unittest

from depviz16.maven import (
    extract_dependencies,
    get_direct_dependencies,
    package_url,
)

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <groupId>com.example</groupId>
    <artifactId>app</artifactId>
    <version>2.0.0</version>
    <properties>
        <lib.version>1.5.0</lib.version>
    </properties>
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.managed</groupId>
                <artifactId>managed-lib</artifactId>
                <version>3.2.1</version>
            </dependency>
        </dependencies>
    </dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.plain</groupId>
            <artifactId>plain-lib</artifactId>
            <version>${lib.version}</version>
        </dependency>
        <dependency>
            <groupId>org.managed</groupId>
            <artifactId>managed-lib</artifactId>
        </dependency>
        <dependency>
            <groupId>org.test</groupId>
            <artifactId>test-lib</artifactId>
            <version>1.0</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.provided</groupId>
            <artifactId>provided-lib</artifactId>
            <version>1.0</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.optional</groupId>
            <artifactId>optional-lib</artifactId>
            <version>1.0</version>
            <optional>true</optional>
        </dependency>
    </dependencies>
</project>
"""


class ExtractDependenciesTest(unittest.TestCase):
    """Проверка извлечения прямых зависимостей и версий."""

    def test_only_runtime_dependencies(self):
        versions = {}
        deps = extract_dependencies(POM, "test", versions)
        self.assertEqual(
            deps, ["org.managed:managed-lib", "org.plain:plain-lib"]
        )

    def test_versions_resolved(self):
        versions = {}
        extract_dependencies(POM, "test", versions)
        self.assertEqual(versions["org.plain:plain-lib"], "1.5.0")
        self.assertEqual(versions["org.managed:managed-lib"], "3.2.1")

    def test_dependency_management_not_an_edge(self):
        deps = extract_dependencies(POM, "test")
        self.assertNotIn("org.managed:unused-lib", deps)

    def test_package_url_with_version(self):
        url = package_url(
            "https://repo1.maven.org/maven2/",
            "com.google.code.findbugs",
            "jsr305",
            "3.0.2",
        )
        self.assertEqual(
            url,
            "https://repo1.maven.org/maven2/com/google/code/"
            "findbugs/jsr305/3.0.2/jsr305-3.0.2.pom",
        )

    def test_local_repository_records_versions(self):
        versions = {}
        deps = get_direct_dependencies(
            "com.example:demo-app", "examples/local_repo", False,
            None, versions,
        )
        self.assertEqual(
            deps,
            [
                "com.google.guava:guava",
                "org.apache.commons:commons-lang3",
            ],
        )
        self.assertEqual(
            versions["com.google.guava:guava"], "33.0.0-jre"
        )


if __name__ == "__main__":
    unittest.main()
