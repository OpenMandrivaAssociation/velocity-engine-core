Name:		velocity-engine-core
Version:	2.4.1
Release:	1
Summary:	Apache Velocity template engine
Group:		Development/Java
License:	ASL 2.0
URL:		https://velocity.apache.org/engine/
Source0:	https://github.com/apache/velocity-engine/archive/refs/tags/%{version}.tar.gz#/velocity-engine-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	mvn(org.apache.commons:commons-lang3)
BuildRequires:	mvn(org.slf4j:slf4j-api)
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Template engine used by the Maven site renderer. The parser sources are
already generated in the tag. VelocityEngineVersion is filled in during
prep, so the build does not run the templating plugin.

%prep
%autosetup -n velocity-engine-%{version}
# The tag is a reactor. This package is only velocity-engine-core.
# velocity-engine-parent is not packaged.
rm -rf src
mv velocity-engine-core/src src
mv velocity-engine-core/pom.xml pom.xml
python - <<PY
import xml.etree.ElementTree as ET
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def local(tag):
    return tag.split("}", 1)[-1]

def artifact_of(elem):
    for node in elem:
        if local(node.tag) == "artifactId":
            return (node.text or "").strip()
    return ""

tree = ET.parse("pom.xml")
root = tree.getroot()
for node in list(root):
    if local(node.tag) == "parent":
        root.remove(node)

def ensure(name, text, after):
    for node in root:
        if local(node.tag) == name:
            node.text = text
            return
    el = ET.Element("{%s}%s" % (NS, name))
    el.text = text
    idx = 0
    for i, node in enumerate(list(root)):
        if local(node.tag) in after:
            idx = i + 1
    root.insert(idx, el)

ensure("groupId", "org.apache.velocity", ("modelVersion",))
ensure("version", "%{version}", ("artifactId", "groupId", "modelVersion"))
drop = {"javacc-maven-plugin", "templating-maven-plugin", "maven-bundle-plugin"}
for build in list(root):
    if local(build.tag) != "build":
        continue
    for plugins in list(build):
        if local(plugins.tag) != "plugins":
            continue
        for plugin in list(plugins):
            if artifact_of(plugin) in drop:
                plugins.remove(plugin)
tree.write("pom.xml", encoding="utf-8", xml_declaration=True)
PY
mkdir -p src/main/java/org/apache/velocity/runtime
cat > src/main/java/org/apache/velocity/runtime/VelocityEngineVersion.java <<'EOF'
package org.apache.velocity.runtime;

public class VelocityEngineVersion
{
    public static final String VERSION = "%{version}";
}
EOF
rm -rf velocity-engine-core velocity-custom-parser-example \
	velocity-engine-examples velocity-engine-scripting \
	spring-velocity-support

%files -f .mfiles
%doc LICENSE NOTICE README.md
