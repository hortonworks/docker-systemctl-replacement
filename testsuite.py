#! /usr/bin/env python
""" Testcases for docker-systemctl-replacement functionality """

from __future__ import print_function

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "1.0.1472"

## NOTE:
## The testcases 1000...4999 are using a --root=subdir environment
## The testcases 5000...9999 will start a docker container to work.

import subprocess
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import types
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json

logg = logging.getLogger("TESTING")
_python = "/usr/bin/python"
_systemctl_py = "files/docker/systemctl.py"
_cov = ""
_cov_run = "coverage2 run '--omit=*/six.py' --append -- "
_cov_cmd = "coverage2"
_cov3run = "coverage3 run '--omit=*/six.py' --append -- "
_cov3cmd = "coverage3"
_python_coverage = "python-coverage"
_python3coverage = "python3-coverage"
COVERAGE = False

IMAGES = "localhost:5000/testingsystemctl"
CENTOS = "centos:7.3.1611"
UBUNTU = "ubuntu:14.04"
OPENSUSE = "opensuse:42.3"

DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"

def sh____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out
def output2(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:    
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out, run.returncode
def _lines(lines):
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines(text):
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def grep(pattern, lines):
    for line in _lines(lines):
       if re.search(pattern, line.rstrip()):
           yield line.rstrip()
def greps(lines, pattern):
    return list(grep(pattern, lines))

def download(base_url, filename, into):
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        sh____("cd {into} && wget {base_url}/{filename}".format(**locals()))
def text_file(filename, content):
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
def shell_file(filename, content):
    text_file(filename, content)
    os.chmod(filename, 0770)
def copy_file(filename, target):
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename, target):
    copy_file(filename, target)
    os.chmod(target, 0750)

def get_caller_name():
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_name():
    frame = inspect.currentframe().f_back.f_back.f_back
    return frame.f_code.co_name
def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
       path = path[1:]
    return os.path.join(root, path)


class DockerSystemctlReplacementTest(unittest.TestCase):
    def caller_testname(self):
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix = None):
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self):
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 5000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname = None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def coverage(self, testname = None):
        testname = testname or self.caller_testname()
        newcoverage = ".coverage."+testname
        time.sleep(1) # TODO: flush output
        if os.path.isfile(".coverage"):
            # shutil.copy(".coverage", newcoverage)
            f = open(".coverage")
            text = f.read()
            f.close()
            text2 = re.sub(r"(\]\}\})[^{}]*(\]\}\})$", r"\1", text)
            f = open(newcoverage, "w")
            f.write(text2)
            f.close()
    def root(self, testdir):
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def user(self):
        import getpass
        getpass.getuser()
    def ip_container(self, name):
        values = output("docker inspect "+name)
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"]    
    def with_local_centos_mirror(self, ver = None):
        """ detects a local centos mirror or starts a local
            docker container with a centos repo mirror. It
            will return the setting for extrahosts"""
        rmi = "localhost:5000"
        rep = "centos-repo"
        ver = ver or "7.3.1611"
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            cmd = "docker rm --force {rep}{ver}"
            sx____(cmd.format(**locals()))
            cmd = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            sh____(cmd.format(**locals()))
        running = output("docker ps")
        if greps(running, rep+ver):
            ip_a = self.ip_container(rep+ver)
            logg.info("%s%s => %s", rep, ver, ip_a)
            result = "mirrorlist.centos.org:%s" % ip_a
            logg.info("--add-host %s", result)
            return result
        return ""
    def with_local_opensuse_mirror(self, ver = None):
        """ detects a local opensuse mirror or starts a local
            docker container with a centos repo mirror. It
            will return the extra_hosts setting to start
            other docker containers"""
        rmi = "localhost:5000"
        rep = "opensuse-repo"
        ver = ver or "42.2"
        find_repo_image = "docker images {rmi}/{rep}:{ver}"
        images = output(find_repo_image.format(**locals()))
        running = output("docker ps")
        if greps(images, rep) and not greps(running, rep+ver):
            cmd = "docker rm --force {rep}{ver}"
            sx____(cmd.format(**locals()))
            cmd = "docker run --detach --name {rep}{ver} {rmi}/{rep}:{ver}"
            sh____(cmd.format(**locals()))
        running = output("docker ps")
        if greps(running, rep+ver):
            ip_a = self.ip_container(rep+ver)
            logg.info("%s%s => %s", rep, ver, ip_a)
            result = "download.opensuse.org:%s" % ip_a
            logg.info("--add-host %s", result)
            return result
        return ""
    def local_image(self, image):
        if image.startswith("centos:"):
            version = image[len("centos:"):]
            add_hosts = self.with_local_centos_mirror(version)
            if add_hosts:
                return "--add-host '{add_hosts}' {image}".format(**locals())
        if image.startswith("opensuse:"):
            version = image[len("opensuse:"):]
            add_hosts = self.with_local_opensuse_mirror(version)
            if add_hosts:
                return "--add-host '{add_hosts}' {image}".format(**locals())
        return image
    def drop_container(self, name):
        cmd = "docker rm --force {name}"
        sx____(cmd.format(**locals()))
    def drop_centos(self):
        self.drop_container("centos")
    def drop_ubuntu(self):
        self.drop_container("ubuntu")
    def drop_opensuse(self):
        self.drop_container("opensuse")
    def make_opensuse(self):
        self.make_container("opensuse", OPENSUSE)
    def make_ubuntu(self):
        self.make_container("ubuntu", UBUNTU)
    def make_centos(self):
        self.make_container("centos", CENTOS)
    def make_container(self, name, image):
        self.drop_container(name)
        local_image = self.local_image(image)
        cmd = "docker run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # " + local_image)
        print("  docker exec -it "+name+" bash")
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_1000(self):
        self.with_local_centos_mirror()
    def test_1001_systemctl_testfile(self):
        """ the systemctl.py file to be tested does exist """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s",  root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(_systemctl_py, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
        self.coverage()
    def test_1002_systemctl_version(self):
        systemctl = _cov + _systemctl_py 
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 0"))
        self.assertTrue(greps(out, "[(]systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
        self.coverage()
    def test_1003_systemctl_help(self):
        """ the '--help' option and 'help' command do work """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} --help"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "{systemctl} help" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "--verbose"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
        self.coverage()
    def test_1005_systemctl_help_command(self):
        """ for any command, 'help command' shows the documentation """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} help list-unit-files" 
        out, end = output2(cmd.format(**locals()))
        logg.info("%s\n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "for more information"))
        self.assertTrue(greps(out, "--type=service"))
        self.coverage()
    def test_1006_systemctl_help_command_other(self):
        """ for a non-existant command, 'help command' just shows the list """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} help list-foo" 
        out, end = output2(cmd.format(**locals()))
        logg.info("%s\n%s", cmd, out)
        self.assertEqual(end, 1)
        self.assertFalse(greps(out, "for more information"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
        self.coverage()
    def test_1010_systemctl_daemon_reload(self):
        """ daemon-reload always succeeds (does nothing) """
        systemctl = _cov + _systemctl_py
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        self.coverage()
    def test_1011_systemctl_daemon_reload_root_ignored(self):
        """ daemon-reload always succeeds (does nothing) """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            ExecStart=/usr/bin/sleep 3
        """)
        cmd = "{systemctl} daemon-reload"
        out,end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        self.rm_testdir()
        self.coverage()
    def test_1020_systemctl_with_systemctl_log(self):
        """ when /var/log/systemctl.log exists then print INFO messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(greps(open(logfile), " INFO ")), 2)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 0)
        self.rm_testdir()
        self.coverage()
    def test_1021_systemctl_with_systemctl_debug_log(self):
        """ when /var/log/systemctl.debug.log exists then print DEBUG messages into it"""
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/systemctl.debug.log")
        text_file(logfile,"")
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(greps(open(logfile), " INFO ")), 2)
        self.assertEqual(len(greps(open(logfile), " DEBUG ")), 3)
        self.rm_testdir()
        self.coverage()
    def test_1030_systemctl_force_ipv4(self):
        """ we can force --ipv4 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/hosts"),"""
            127.0.0.1 localhost localhost4
            ::1 localhost localhost6""")
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        #
        cmd = "{systemctl} --ipv4 daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertFalse(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
        self.coverage()
    def test_1031_systemctl_force_ipv6(self):
        """ we can force --ipv6 for /etc/hosts """
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/hosts"),"""
            127.0.0.1 localhost localhost4
            ::1 localhost localhost6""")
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        #
        cmd = "{systemctl} --ipv6 daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(lines(out), [])
        self.assertEqual(end, 0)
        hosts = open(os_path(root, "/etc/hosts")).read()
        self.assertEqual(len(lines(hosts)), 2)
        self.assertTrue(greps(hosts, "127.0.0.1.*localhost4"))
        self.assertTrue(greps(hosts, "::1.*localhost6"))
        self.assertFalse(greps(hosts, "127.0.0.1.*localhost "))
        self.assertTrue(greps(hosts, "::1.*localhost "))
        self.rm_testdir()
        self.coverage()
    def test_1050_can_create_a_test_service(self):
        """ check that a unit file can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertIn("\nDescription", textA)
        self.rm_testdir()
        self.coverage()
    def test_1051_can_parse_the_service_file(self):
        """ check that a unit file can be parsed atleast for a description """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        cmd = "{systemctl} __get_description a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "Testing A"))
        self.rm_testdir()
        self.coverage()
    def test_1052_can_describe_a_pid_file(self):
        """ check that a unit file can have a specific pdi file """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "/var/run/foo.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1053_can_have_default_pid_file_for_simple_service(self):
        """ check that a unit file has a default pid file for simple services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertFalse(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "/var/run/a.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1055_other_services_use_a_status_file(self):
        """ check that other unit files may have a default status file """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=oneshot
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertFalse(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_status_file a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "/var/run/a.service.status"))
        self.rm_testdir()
        self.coverage()
    def test_1060_can_have_shell_like_commments(self):
        """ check that a unit file can have comment lines with '#' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            #PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "/var/run/foo.pid"))
        self.assertTrue(greps(out, "/var/run/a.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1061_can_have_winini_like_commments(self):
        """ check that a unit file can have comment lines with ';' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            ;PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_pid_file a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "/var/run/foo.pid"))
        self.assertTrue(greps(out, "/var/run/a.service.pid"))
        self.rm_testdir()
        self.coverage()
    def test_1062_can_have_multi_line_settings_with_linebreak_mark(self):
        """ check that a unit file can have settings with '\\' at the line end """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A \
                which is quite special
            [Service]
            PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "quite special"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_description a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "Testing A"))
        self.assertTrue(greps(out, "quite special"))
        self.rm_testdir()
        self.coverage()
    def test_1063_but_a_missing_linebreak_is_a_syntax_error(self):
        """ check that a unit file can have 'bad ini' lines throwing an exception """
        # the original systemd daemon would ignore services with syntax errors
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A 
                which is quite special
            [Service]
            PIDFile=/var/run/foo.pid
            """)
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textA, "quite special"))
        self.assertTrue(greps(textA, "PIDFile="))
        cmd = "{systemctl} __get_description a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "Testing A"))
        self.assertFalse(greps(out, "quite special"))
        self.rm_testdir()
        self.coverage()
    def test_1070_external_env_files_can_be_parsed(self):
        """ check that a unit file can have a valid EnvironmentFile for settings """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A 
                which is quite special
            [Service]
            EnvironmentFile=/etc/sysconfig/a.conf
            """)
        text_file(os_path(root, "/etc/sysconfig/a.conf"),"""
            CONF1=a1
            CONF2="b2"
            CONF3='c3'
            #CONF4=b4
            """)
        cmd = "{systemctl} __read_env_file /etc/sysconfig/a.conf -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s => \n%s", cmd, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "CONF1"))
        self.assertTrue(greps(out, "CONF2"))
        self.assertTrue(greps(out, "CONF3"))
        self.assertFalse(greps(out, "CONF4"))
        self.assertTrue(greps(out, "a1"))
        self.assertTrue(greps(out, "b2"))
        self.assertTrue(greps(out, "c3"))
        self.assertFalse(greps(out, '"b2"'))
        self.assertFalse(greps(out, "'c3'"))
        self.rm_testdir()
        self.coverage()
    def test_1080_preset_files_can_be_parsed(self):
        """ check that preset files do work internally"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} __load_preset_files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} __get_preset_of_unit a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        # self.assertTrue(greps(out, r"^our.preset"))
        self.assertEqual(len(lines(out)), 0)
        #
        cmd = "{systemctl} __get_preset_of_unit b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enable"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} __get_preset_of_unit c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disable"))
        self.assertEqual(len(lines(out)), 1)
    def test_1090_syntax_errors_are_shown_on_daemon_reload(self):
        """ check that preset files do work internally"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=foo
            ExecStart=runA
            ExecReload=runB
            ExecStop=runC
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            type=simple
            ExecReload=/usr/bin/kill -SIGHUP $MAINPID
            ExecStop=/usr/bin/kill $MAINPID
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/d.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            type=forking
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/g.service"),"""
            [Unit]
            Description=Testing G
            [Service]
            Type=foo
            ExecStart=runA
            ExecStart=runA2
            ExecReload=runB
            ExecReload=runB2
            ExecStop=runC
            ExecStop=runC2
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} daemon-reload -vv 2>&1"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service:.* file without .Service. section"))
        self.assertTrue(greps(out, r"b.service:.* Executable path is not absolute"))
        self.assertTrue(greps(out, r"c.service: Service has no ExecStart"))
        self.assertTrue(greps(out, r"d.service: Service lacks both ExecStart and ExecStop"))
        self.assertTrue(greps(out, r"g.service: there may be only one ExecStart statement"))
        self.assertTrue(greps(out, r"g.service: there may be only one ExecStop statement"))
        self.assertTrue(greps(out, r"g.service: there may be only one ExecReload statement"))
        self.assertTrue(greps(out, r"c.service: the use of /bin/kill is not recommended"))
    def test_2001_can_create_test_services(self):
        """ check that two unit files can be created for testing """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        textA = file(os_path(root, "/etc/systemd/system/a.service")).read()
        textB = file(os_path(root, "/etc/systemd/system/b.service")).read()
        self.assertTrue(greps(textA, "Testing A"))
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textA)
        self.assertIn("\nDescription", textB)
        self.rm_testdir()
        self.coverage()
    def test_2002_list_units(self):
        """ check that two unit files can be found for 'list-units' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} list-units"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertIn("loaded units listed.", out)
        self.assertIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend list-units"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+loaded inactive dead\s+.*Testing A"))
        self.assertTrue(greps(out, r"b.service\s+loaded inactive dead\s+.*Testing B"))
        self.assertNotIn("loaded units listed.", out)
        self.assertNotIn("To show all installed unit files use", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2003_list_unit_files(self):
        """ check that two unit service files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2004_list_unit_files_wanted(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 5)
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertNotIn("unit files listed.", out)
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2006_list_unit_files_wanted_and_unknown_type(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status plus handling unkonwn services"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=foo list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertIn("0 unit files listed.", out)
        self.assertEqual(len(lines(out)), 3)
        self.rm_testdir()
        self.coverage()
    def test_2008_list_unit_files_locations(self):
        """ check that unit files can be found for 'list-unit-files'
            in different standard locations on disk. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/usr/lib/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/lib/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/var/run/systemd/system/d.service"),"""
            [Unit]
            Description=Testing D
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+disabled"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertTrue(greps(out, r"c.service\s+disabled"))
        self.assertTrue(greps(out, r"d.service\s+disabled"))
        self.assertIn("4 unit files listed.", out)
        self.assertEqual(len(lines(out)), 7)
        #
        cmd = "{systemctl} enable a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable d.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+enabled"))
        self.assertTrue(greps(out, r"b.service\s+enabled"))
        self.assertTrue(greps(out, r"c.service\s+enabled"))
        self.assertTrue(greps(out, r"d.service\s+enabled"))
        self.assertIn("4 unit files listed.", out)
        self.assertEqual(len(lines(out)), 7)
        #
        self.rm_testdir()
        self.coverage()
    def test_2013_list_unit_files_common_targets(self):
        """ check that some unit target files can be found for 'list-unit-files' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertFalse(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "{systemctl} --no-legend --type=target list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, r"a.service\s+static"))
        self.assertFalse(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertGreater(len(lines(out)), 10)
        num_targets = len(lines(out))
        cmd = "{systemctl} --no-legend list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+static"))
        self.assertTrue(greps(out, r"multi-user.target\s+enabled"))
        self.assertEqual(len(lines(out)), num_targets + 2)
        self.rm_testdir()
        self.coverage()
    def test_2014_list_unit_files_now(self):
        """ check that 'list-unit-files --now' presents a special debug list """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B""")
        cmd = "{systemctl} --no-legend --now list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+SysD\s+.*systemd/system/a.service"))
        self.assertTrue(greps(out, r"b.service\s+SysD\s+.*systemd/system/b.service"))
        self.assertFalse(greps(out, r"multi-user.target"))
        self.assertFalse(greps(out, r"enabled"))
        self.assertEqual(len(lines(out)), 2)
        self.rm_testdir()
        self.coverage()
    def test_2020_show_unit_is_parseable(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        num_lines = len(lines(out))
        #
        cmd = "{systemctl} --all show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertGreater(len(lines(out)), num_lines)
        #
        for line in lines(out):
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2021_show_unit_can_be_restricted_to_one_property(self):
        """ check that 'show UNIT' may return just one value if asked for"""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        cmd = "{systemctl} show a.service --property=Description"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=Description --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Description="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=PIDFile"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} show a.service --property=PIDFile --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertEqual(len(lines(out)), 1)
        #
        self.assertEqual(lines(out), [ "PIDFile=" ])
        self.rm_testdir()
        self.coverage()
    def test_2025_show_unit_for_multiple_matches(self):
        """ check that the result of 'show UNIT' for multiple services is 
            concatenated but still machine readable. """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        a_lines = len(lines(out))
        #
        cmd = "{systemctl} show b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        b_lines = len(lines(out))
        #
        cmd = "{systemctl} show a.service b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        all_lines = len(lines(out))
        #
        self.assertGreater(all_lines, a_lines + b_lines)
        #
        for line in lines(out):
            if not line.strip():
                # empty lines are okay now
                continue
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2027_show_unit_for_oneshot_service(self):
        """ check that 'show UNIT' is machine-readable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=oneshot
            ExecStart=/bin/echo foo
            ExecStop=/bin/echo bar
            """)
        cmd = "{systemctl} show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState="))
        num_lines = len(lines(out))
        #
        cmd = "{systemctl} --all show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^Id="))
        self.assertTrue(greps(out, r"^Names="))
        self.assertTrue(greps(out, r"^Description="))
        self.assertTrue(greps(out, r"^MainPID="))
        self.assertTrue(greps(out, r"^LoadState="))
        self.assertTrue(greps(out, r"^ActiveState="))
        self.assertTrue(greps(out, r"^SubState="))
        self.assertTrue(greps(out, r"^UnitFileState=static"))
        self.assertTrue(greps(out, r"^PIDFile="))
        self.assertGreater(len(lines(out)), num_lines)
        #
        for line in lines(out):
            m = re.match(r"^\w+=", line)
            if not m:
                # found non-machine readable property line
                self.assertEqual("word=value", line)
        self.rm_testdir()
        self.coverage()
    def test_2030_show_unit_display_parsed_timeouts(self):
        """ check that 'show UNIT' show parsed timeoutss """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=29
            TimeoutStopSec=60
            """)
        cmd = "{systemctl} show a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=29s", rep)
        self.assertIn("TimeoutStopUSec=1min", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=1m
            TimeoutStopSec=2min
            """)
        cmd = "{systemctl} show b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min", rep)
        self.assertIn("TimeoutStopUSec=2min", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=1s
            TimeoutStopSec=2000ms
            """)
        cmd = "{systemctl} show c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1s", rep)
        self.assertIn("TimeoutStopUSec=2s", rep)
        #
        self.rm_testdir()
        self.coverage()
        ##
        text_file(os_path(root, "/etc/systemd/system/d.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=90s
            TimeoutStopSec=2250ms
            """)
        cmd = "{systemctl} show d.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min 30s", rep)
        self.assertIn("TimeoutStopUSec=2s 250ms", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/e.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=90s 250ms
            TimeoutStopSec=3m 25ms
            """)
        cmd = "{systemctl} show e.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=1min 30s 250ms", rep)
        self.assertIn("TimeoutStopUSec=3min 25ms", rep)
        ##
        text_file(os_path(root, "/etc/systemd/system/f.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            TimeoutStartSec=180
            TimeoutStopSec=182
            """)
        cmd = "{systemctl} show f.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        rep = lines(out)
        self.assertIn("TimeoutStartUSec=3min", rep)
        self.assertIn("TimeoutStopUSec=3min 2s", rep)
        #
        self.rm_testdir()
        self.coverage()
    def test_2140_show_environment_from_parts(self):
        """ check that the result of 'environment UNIT' can 
            list the settings from different locations."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/sysconfig/b.conf"),"""
            DEF1='def1'
            DEF2="def2"
            DEF3=def3
            """)
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/b.conf
            Environment=DEF5=def5
            Environment=DEF6=def6
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \
                                $DEF3 $DEF4 $DEF5
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} environment b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2"))
        self.assertTrue(greps(out, r"^DEF3=def3"))
        self.assertFalse(greps(out, r"^DEF4=def4"))
        self.assertTrue(greps(out, r"^DEF5=def5"))
        self.assertTrue(greps(out, r"^DEF6=def6"))
        self.assertFalse(greps(out, r"^DEF7=def7"))
        a_lines = len(lines(out))
        #
        self.rm_testdir()
        self.coverage()
    def test_2150_have_environment_with_multiple_parts(self):
        """ check that the result of 'environment UNIT' can 
            list the assignements that are crammed into one line."""
        # https://www.freedesktop.org/software/systemd/man/systemd.exec.html#Environment=
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/sysconfig/b.conf"),"""
            DEF1='def1'
            DEF2="def2"
            DEF3=def3
            """)
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/b.conf
            Environment="VAR1=word1 word2" VAR2=word3 "VAR3=$word 5 6"
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \
                                $VAR1 $VAR2 $VAR3
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} environment b.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2"))
        self.assertTrue(greps(out, r"^DEF3=def3"))
        self.assertTrue(greps(out, r"^VAR1=word1 word2"))
        self.assertTrue(greps(out, r"^VAR2=word3"))
        self.assertTrue(greps(out, r"^VAR3=\$word 5 6"))
        a_lines = len(lines(out))
        #
        self.rm_testdir()
        self.coverage()
    def test_2900_class_UnitConfParser(self):
        """ using systemctl.py as a helper library for 
            the UnitConfParser functions."""
        python = _python
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl_py_dir = os.path.dirname(os.path.realpath(_systemctl_py))
        unitconfparser_py = os_path(root, "/usr/bin/unitconfparser.py")
        service_file = os_path(root, "/etc/systemd/system/b.service")
        defaults = {"a1": "default1"}
        shell_file(unitconfparser_py,"""
            #! {python}
            from __future__ import print_function
            import sys
            sys.path += [ "{systemctl_py_dir}" ]
            import systemctl
            parser = systemctl.UnitConfigParser({defaults})
            print("DEFAULTS", parser.defaults())
            print("FILENAME", parser.filename())
            parser.read(sys.argv[1])
            print("filename=", parser.filename())
            print("sections=", parser.sections())
            print("has.Foo.Bar=", parser.has_option("Foo", "Bar"))
            print("has.Unit.Foo=", parser.has_option("Unit", "Foo"))
            try:
               parser.get("Foo", "Bar")
            except Exception as e:
               print("get.Foo.Bar:", str(e))
            try:
               parser.get("Unit", "Foo")
            except Exception as e:
               print("get.Unit.Foo:", str(e))
            try:
               parser.getlist("Foo", "Bar")
            except Exception as e:
               print("getlist.Foo.Bar:", str(e))
            try:
               parser.getlist("Unit", "Foo")
            except Exception as e:
               print("getlist.Unit.Foo:", str(e))
            print("get.none.Foo.Bar=", parser.get("Foo", "Bar", allow_no_value = True))
            print("get.none.Unit.Foo=", parser.get("Unit", "Foo", allow_no_value = True))
            print("getlist.none.Foo.Bar=", parser.getlist("Foo", "Bar", allow_no_value = True))
            print("getlist.none.Unit.Foo=", parser.getlist("Unit", "Foo", allow_no_value = True))
            print("get.defs.Foo.Bar=", parser.get("Foo", "Bar", "def1"))
            print("get.defs.Unit.Foo=", parser.get("Unit", "Foo", "def2"))
            print("getlist.defs.Foo.Bar=", parser.getlist("Foo", "Bar", ["def3"]))
            print("getlist.defs.Unit.Foo=", parser.getlist("Unit", "Foo", ["def4"]))
            parser.set("Unit", "After", "network.target")
            print("getlist.unit.after1=", parser.getlist("Unit", "After"))
            print("getitem.unit.after1=", parser.get("Unit", "After"))
            parser.set("Unit", "After", "postgres.service")
            print("getlist.unit.after2=", parser.getlist("Unit", "After"))
            print("getitem.unit.after2=", parser.get("Unit", "After"))
            parser.set("Unit", "After", None)
            print("getlist.unit.after0=", parser.getlist("Unit", "After"))
            print("getitem.unit.after0=", parser.get("Unit", "After", allow_no_value = True))
            print("getlist.environment=", parser.getlist("Service", "Environment"))
            print("get.environment=", parser.get("Service", "Environment"))
            print("get.execstart=", parser.get("Service", "ExecStart"))
            """.format(**locals()))
        text_file(service_file,"""
            [Unit]
            Description=Testing B
            [Service]
            EnvironmentFile=/etc/sysconfig/b.conf
            Environment=DEF5=def5
            Environment=DEF6=def6
            ExecStart=/usr/bin/printf $DEF1 $DEF2 \\
                                $DEF3 $DEF4 $DEF5 \\
                                $DEF6 $DEF7
            [Install]
            WantedBy=multi-user.target""")
        testrun = _cov + unitconfparser_py
        cmd = "{testrun} {service_file}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "DEFAULTS {'a1': 'default1'}"))
        self.assertTrue(greps(out, "FILENAME None"))
        self.assertTrue(greps(out, "filename= .*"+service_file))
        self.assertTrue(greps(out, "sections= \\['Unit', 'Service', 'Install'\\]"))
        self.assertTrue(greps(out, "has.Foo.Bar= False"))
        self.assertTrue(greps(out, "has.Unit.Foo= False"))
        self.assertTrue(greps(out, "get.Foo.Bar: section Foo does not exist"))
        self.assertTrue(greps(out, "get.Unit.Foo: option Foo in Unit does not exist"))
        self.assertTrue(greps(out, "getlist.Foo.Bar: section Foo does not exist"))
        self.assertTrue(greps(out, "getlist.Unit.Foo: option Foo in Unit does not exist"))
        self.assertTrue(greps(out, "get.none.Foo.Bar= None"))
        self.assertTrue(greps(out, "get.none.Unit.Foo= None"))
        self.assertTrue(greps(out, "getlist.none.Foo.Bar= \\[\\]"))
        self.assertTrue(greps(out, "getlist.none.Unit.Foo= \\[\\]"))
        self.assertTrue(greps(out, "get.defs.Foo.Bar= def1"))
        self.assertTrue(greps(out, "get.defs.Unit.Foo= def2"))
        self.assertTrue(greps(out, "getlist.defs.Foo.Bar= \\['def3'\\]"))
        self.assertTrue(greps(out, "getlist.defs.Unit.Foo= \\['def4'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after1= \\['network.target'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after2= \\['network.target', 'postgres.service'\\]"))
        self.assertTrue(greps(out, "getlist.unit.after0= \\[\\]"))
        self.assertTrue(greps(out, "getitem.unit.after1= network.target"))
        self.assertTrue(greps(out, "getitem.unit.after2= network.target"))
        self.assertTrue(greps(out, "getitem.unit.after0= None"))
        self.assertTrue(greps(out, "getlist.environment= \\['DEF5=def5', 'DEF6=def6'\\]"))
        self.assertTrue(greps(out, "get.environment= DEF5=def5"))
        self.assertTrue(greps(out, "get.execstart= /usr/bin/printf \\$DEF1 \\$DEF2 \\\\$"))
        self.assertTrue(greps(out, "      \\$DEF3 \\$DEF4 \\$DEF5"))
        self.assertTrue(greps(out, "      \\$DEF6 \\$DEF7"))
        #
        self.rm_testdir()
        self.coverage()
    def test_3002_enable_service_creates_a_symlink(self):
        """ check that a service can be enabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        self.rm_testdir()
        self.coverage()
    def test_3003_disable_service_removes_the_symlink(self):
        """ check that a service can be enabled and disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        textB = file(enabled_file).read()
        self.assertTrue(greps(textB, "Testing B"))
        self.assertIn("\nDescription", textB)
        #
        cmd = "{systemctl} enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} enable other.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/other.service")
        self.assertFalse(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} disable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} disable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} disable other.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        #
        self.rm_testdir()
        self.coverage()
    def test_3004_list_unit_files_when_enabled(self):
        """ check that two unit files can be found for 'list-unit-files'
            with an enabled status """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertTrue(os.path.islink(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend disable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        enabled_file = os_path(root, "/etc/systemd/system/multi-user.target.wants/b.service")
        self.assertFalse(os.path.exists(enabled_file))
        #
        cmd = "{systemctl} --no-legend --type=service list-unit-files"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"a.service\s+static"))
        self.assertTrue(greps(out, r"b.service\s+disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        self.rm_testdir()
        self.coverage()
    def test_3005_is_enabled_result_when_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} --no-legend disable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3006_is_enabled_is_true_when_any_is_enabled(self):
        """ check that 'is-enabled' reports correctly for enabled/disabled """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        cmd = "{systemctl} is-enabled b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        cmd = "{systemctl} is-enabled a.service b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertFalse(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 3)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} is-enabled b.service a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} is-enabled c.service a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^static"))
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 2)
        #
        self.rm_testdir()
        self.coverage()
    def test_3009_sysv_service_enable(self):
        """ check that we manage SysV services in a root env
            with basic enable/disable commands, also being
            able to check its status."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "xxx.init"), """
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network 
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
        """)
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network 
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
            logfile={logfile}
            sleeptime=50
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "xxx.init"), os_path(root, "/etc/init.d/xxx"))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/etc/init.d/zzz"))
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} enable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        self.assertEqual(end, 0)
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} --no-legend disable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} disable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} disable xxx.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(len(lines(out)), 0)
        #
        self.rm_testdir()
        self.coverage()

    def test_3010_check_preset_all(self):
        """ check that 'is-enabled' reports correctly after 'preset-all' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset-all" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3011_check_preset_one(self):
        """ check that 'is-enabled' reports correctly after 'preset service' """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset c.service -vv" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3012_check_preset_to_reset_one(self):
        """ check that 'enable' and 'preset service' are counterparts """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3013_check_preset_to_reset_some(self):
        """ check that 'enable' and 'preset services..' are counterparts """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset b.service c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset b.service c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} preset b.service c.service other.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3015_check_preset_all_only_enable(self):
        """ check that 'preset-all' works with --preset-mode=enable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset-all --preset-mode=enable" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
        self.coverage()
    def test_3016_check_preset_all_only_disable(self):
        """ check that 'preset-all' works with --preset-mode=disable """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable b.service
            disable c.service""")
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        cmd = "{systemctl} disable b.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable c.service" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^enabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} preset-all --preset-mode=disable" 
        logg.info(" %s", cmd.format(**locals()))
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} is-enabled a.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^static"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-enabled b.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-enabled c.service" 
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, r"^disabled"))
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 1)
        #
        self.rm_testdir()
        self.coverage()
    def test_3020_default_services(self):
        """ check the 'default-services' to know the enabled services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        self.assertFalse(greps(out, "a.service"))
        self.assertTrue(greps(out, "b.service"))
        self.assertTrue(greps(out, "c.service"))
        #
        self.rm_testdir()
        self.coverage()
    def test_3021_default_services(self):
        """ check that 'default-services' skips some known services """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        text_file(os_path(root, "/etc/systemd/system/a.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/c.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/mount-disks.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(root, "/etc/systemd/system/network.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 0)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable b.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable c.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable mount-disks.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} --no-legend enable network.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 2)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 3)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} default-services --all --force"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(len(lines(out)), 4)
        self.assertEqual(end, 0)
        #
        self.rm_testdir()
        self.coverage()
    def test_3030_systemctl_py_start_simple(self):
        """ check that we can start simple services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3031_systemctl_py_start_extra_simple(self):
        """ check that we can start extra simple services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3032_systemctl_py_start_forking(self):
        """ check that we can start forking services with root env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall {testsleep}
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExceStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3033_systemctl_py_start_forking_without_pid_file(self):
        """ check that we can start forking services with root env without PIDFile"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &) &
               wait %1
               # ps -o pid,ppid,args >&2
            ;; stop)
               killall {testsleep}
               echo killed all {testsleep} >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} enable zzz.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3041_systemctl_py_run_default_services_in_testenv(self):
        """ check that we can enable services in a test env to be run as default-services"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        cmd = "{systemctl} enable zzb.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} enable zzc.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} default-services -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzb.service"))
        self.assertEqual(len(lines(out)), 2)
        #
        cmd = "{systemctl} default -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        self.assertTrue(greps(top, testsleep+" 50"))
        #
        cmd = "{systemctl} halt -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)        
        self.assertFalse(greps(top, testsleep))
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3050_systemctl_py_check_is_active_in_testenv(self):
        """ check is_active behaviour in local testenv env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        is_active_A = "{systemctl} is-active zza.service"
        is_active_B = "{systemctl} is-active zzb.service"
        is_active_C = "{systemctl} is-active zzc.service"
        is_active_D = "{systemctl} is-active zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "active")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertNotEqual(exitD, 0)
        #
        logg.info("== checking combinations of arguments")
        is_active_BC = "{systemctl} is-active zzb.service zzc.service "
        is_active_CD = "{systemctl} is-active zzc.service zzd.service"
        is_active_BD = "{systemctl} is-active zzb.service zzd.service"
        is_active_BCD = "{systemctl} is-active zzb.service zzc.service zzd.service"
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        actCD, exitCD  = output2(is_active_CD.format(**locals()))
        actBD, exitBD  = output2(is_active_BD.format(**locals()))
        actBCD, exitBCD  = output2(is_active_BCD.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "inactive", ""])
        self.assertEqual(actCD.split("\n"), [ "inactive", "unknown",""])
        self.assertEqual(actBD.split("\n"), [ "active", "unknown", ""])
        self.assertEqual(actBCD.split("\n"), ["active", "inactive", "unknown", ""])
        self.assertNotEqual(exitBC, 0)         ## this is how the original systemctl
        self.assertNotEqual(exitCD, 0)         ## works. The documentation however
        self.assertNotEqual(exitBD, 0)         ## says to return 0 if any service
        self.assertNotEqual(exitBCD, 0)        ## is found to be 'active'
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertEqual(exitBC, 0)         ## all is-active => return 0
        #
        cmd = "{systemctl} stop zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3051_systemctl_py_check_is_failed_in_testenv(self):
        """ check is_failed behaviour in local testenv env"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "inactive")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertEqual(exitD, 0)
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        is_active_A = "{systemctl} is-failed zza.service"
        is_active_B = "{systemctl} is-failed zzb.service"
        is_active_C = "{systemctl} is-failed zzc.service"
        is_active_D = "{systemctl} is-failed zzd.service"
        actA, exitA  = output2(is_active_A.format(**locals()))
        actB, exitB  = output2(is_active_B.format(**locals()))
        actC, exitC  = output2(is_active_C.format(**locals()))
        actD, exitD  = output2(is_active_D.format(**locals()))
        self.assertEqual(actA.strip(), "inactive")
        self.assertEqual(actB.strip(), "active")
        self.assertEqual(actC.strip(), "inactive")
        self.assertEqual(actD.strip(), "unknown")
        self.assertNotEqual(exitA, 0)
        self.assertNotEqual(exitB, 0)
        self.assertNotEqual(exitC, 0)
        self.assertEqual(exitD, 0)
        #
        logg.info("== checking combinations of arguments")
        is_active_BC = "{systemctl} is-failed zzb.service zzc.service "
        is_active_CD = "{systemctl} is-failed zzc.service zzd.service"
        is_active_BD = "{systemctl} is-failed zzb.service zzd.service"
        is_active_BCD = "{systemctl} is-failed zzb.service zzc.service zzd.service"
        is_active_BCDX = "{systemctl} is-failed zzb.service zzc.service zzd.service --quiet"
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        actCD, exitCD  = output2(is_active_CD.format(**locals()))
        actBD, exitBD  = output2(is_active_BD.format(**locals()))
        actBCD, exitBCD  = output2(is_active_BCD.format(**locals()))
        actBCDX, exitBCDX  = output2(is_active_BCDX.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "inactive", ""])
        self.assertEqual(actCD.split("\n"), [ "inactive", "unknown",""])
        self.assertEqual(actBD.split("\n"), [ "active", "unknown", ""])
        self.assertEqual(actBCD.split("\n"), ["active", "inactive", "unknown", ""])
        self.assertEqual(actBCDX.split("\n"), [""])
        self.assertNotEqual(exitBC, 0)         ## this is how the original systemctl
        self.assertNotEqual(exitCD, 0)         ## works. The documentation however
        self.assertNotEqual(exitBD, 0)         ## says to return 0 if any service
        self.assertNotEqual(exitBCD, 0)        ## is found to be 'active'
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["active", "active", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["failed", "failed", ""])
        self.assertEqual(exitBC, 0)         ## all is-failed => return 0
        #
        cmd = "{systemctl} stop zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        actBC, exitBC  = output2(is_active_BC.format(**locals()))
        self.assertEqual(actBC.split("\n"), ["inactive", "inactive", ""])
        self.assertNotEqual(exitBC, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3101_missing_environment_file_makes_service_ignored(self):
        """ check that a missing EnvironmentFile spec makes the service to be ignored"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            EnvironmentFile=/foo.conf
            ExecStart={bindir}/{testsleep} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        start_service = "{systemctl} start zzz.service -vv"
        end = sx____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        self.assertGreater(end, 0)
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        end = sx____(stop_service.format(**locals()))
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        self.assertGreater(end, 0)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3111_environment_files_are_included(self):
        """ check that environment specs are read correctly"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            EnvironmentFile=/etc/sysconfig/zzz.conf
            Environment=CONF4=dd4
            ExecStart={bindir}/zzz.sh
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            echo "WITH CONF1=$CONF1" >> {logfile}
            echo "WITH CONF2=$CONF2" >> {logfile}
            echo "WITH CONF3=$CONF3" >> {logfile}
            echo "WITH CONF4=$CONF4" >> {logfile}
            {bindir}/{testsleep} 4
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.conf"),"""
            CONF1=aa1
            CONF2="bb2"
            CONF3='cc3'
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(bindir, "zzz.sh"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_file(os_path(testdir, "zzz.conf"), os_path(root, "/etc/sysconfig/zzz.conf"))
        #
        start_service = "{systemctl} start zzz.service -vv"
        end = sx____(start_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        self.assertEqual(end, 0)
        #
        log = lines(open(logfile))
        logg.info("LOG \n| %s", "\n| ".join(log))
        self.assertTrue(greps(log, "WITH CONF1=aa1"))
        self.assertTrue(greps(log, "WITH CONF2=bb2"))
        self.assertTrue(greps(log, "WITH CONF3=cc3"))
        self.assertTrue(greps(log, "WITH CONF4=dd4"))
        os.remove(logfile)
        #
        stop_service = "{systemctl} stop zzz.service -vv"
        end = sx____(stop_service.format(**locals()))
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        #
        self.rm_testdir()
        self.coverage()
    def test_3140_may_expand_environment_variables(self):
        """ check that different styles of environment
            variables get expanded."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        print_sh = os_path(root, "/usr/bin/print.sh")
        logfile = os_path(root, "/var/log/print_sh.log")
        text_file(os_path(root, "/etc/sysconfig/b.conf"),"""
            DEF1='def1'
            DEF2="def2 def3"
            DEF4="$DEF1 ${DEF2}"
            DEF5="$DEF1111 def5 ${DEF2222}"
            """)
        text_file(os_path(root, "/etc/systemd/system/b.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Environment=DEF2=foo
            EnvironmentFile=/etc/sysconfig/b.conf
            ExecStart=/usr/bin/sleep 2
            ExecStartPost=%s A $DEF1 $DEF2
            ExecStartPost=%s B ${DEF1} ${DEF2}
            ExecStartPost=%s C $DEF1$DEF2
            ExecStartPost=%s D ${DEF1}${DEF2}
            ExecStartPost=%s E ${DEF4}
            ExecStartPost=%s F ${DEF5}
            [Install]
            WantedBy=multi-user.target""" 
            % (print_sh, print_sh, print_sh, print_sh, 
               print_sh, print_sh,))
        text_file(logfile, "")
        shell_file(print_sh, """
            #! /bin/sh
            logfile='{logfile}'
            echo "'$1' '$2' '$3' '$4' '$5'" >> "$logfile"
            """.format(**locals()))
        cmd = "{systemctl} environment b.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"^DEF1=def1"))
        self.assertTrue(greps(out, r"^DEF2=def2 def3"))
        #
        cmd = "{systemctl} start b.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        A="'A' 'def1' 'def2' 'def3' ''"   # A $DEF1 $DEF2
        B="'B' 'def1' 'def2 def3' '' ''"  # B ${DEF1} ${DEF2}
        C="'C' 'def1def2' 'def3' '' ''"   # C $DEF1$DEF2
        D="'D' 'def1def2 def3' '' '' ''"  # D ${DEF1}${DEF2} ??TODO??
        E="'E' 'def1 def2 def3' '' '' ''" # E ${DEF4}
        F="'F' ' def5 ' '' '' ''"         # F ${DEF5}
        self.assertIn(A, log)
        self.assertIn(B, log)
        self.assertIn(C, log)
        self.assertIn(D, log)
        self.assertIn(E, log)
        self.assertIn(F, log)
        #
        self.rm_testdir()
        self.coverage()
    def test_3150_may_expand_special_variables(self):
        """ check that different flavours for special
            variables get expanded."""
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        print_sh = os_path(root, "/usr/bin/print.sh")
        logfile = os_path(root, "/var/log/print_sh.log")
        service_file = os_path(root, "/etc/systemd/system/b c.service")
        text_file(service_file,"""
            [Unit]
            Description=Testing B
            [Service]
            Environment=X=x1
            Environment="Y=y2 y3"
            ExecStart=/usr/bin/sleep 2
            ExecStartPost=%s A %%N $X ${Y}
            ExecStartPost=%s B %%n $X ${Y}
            ExecStartPost=%s C %%f $X ${Y}
            ExecStartPost=%s D %%t $X ${Y}
            ExecStartPost=%s E %%P $X ${Y}
            ExecStartPost=%s F %%p $X ${Y}
            ExecStartPost=%s G %%I $X ${Y}
            ExecStartPost=%s H %%i $X ${Y} $FOO
            ExecStartPost=%s Z %%Z $X ${Y} ${FOO}
            [Install]
            WantedBy=multi-user.target""" 
            % (print_sh, print_sh, print_sh, print_sh,
               print_sh, print_sh, print_sh, print_sh,
               print_sh,))
        text_file(logfile, "")
        shell_file(print_sh, """
            #! /bin/sh
            logfile='{logfile}'
            echo "'$1' '$2' '$3' '$4' '$5'" >> "$logfile"
            """.format(**locals()))
        #
        cmd = "{systemctl} start 'b c.service' -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        log = lines(open(logfile))
        logg.info("LOG \n%s", log)
        A="'A' 'b' 'c.service' 'x1' 'y2 y3'"  # A %%N
        B="'B' 'b c.service' 'x1' 'y2 y3' ''" # B %%n
        C="'C' '%s' 'x1' 'y2 y3' ''" % service_file           # C %%f
        D="'D' '%s' 'x1' 'y2 y3' ''" % os_path(root, "/var")  # D %%t
        E="'E' 'b' 'c' 'x1' 'y2 y3'"  # E %%P
        F="'F' 'b c' 'x1' 'y2 y3' ''" # F %%p
        G="'G' 'x1' 'y2 y3' '' ''" # G %%I
        H="'H' '' 'x1' 'y2 y3' ''" # H %%i
        Z="'Z' '' 'x1' 'y2 y3' ''" # Z %%Z
        self.assertIn(A, log)
        self.assertIn(B, log)
        self.assertIn(C, log)
        self.assertIn(D, log)
        self.assertIn(E, log)
        self.assertIn(F, log)
        self.assertIn(G, log)
        self.assertIn(H, log)
        self.assertIn(Z, log)
        #
        self.rm_testdir()
        self.coverage()
    def test_3201_service_config_cat(self):
        """ check that a name service config can be printed as-is"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} cat zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        orig = lines(open(os_path(root, "/etc/systemd/system/zzs.service")))
        data = lines(out)
        self.assertEqual(orig + [""], data)
        #
        self.rm_testdir()
        self.coverage()
    def test_3203_service_config_cat_plus_unknown(self):
        """ check that a name service config can be printed as-is"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} cat zzs.service unknown.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        orig = lines(open(os_path(root, "/etc/systemd/system/zzs.service")))
        data = lines(out)
        self.assertEqual(orig + [""], data)
        #
        self.rm_testdir()
        self.coverage()
    def test_3301_service_config_show(self):
        """ check that a named service config can show its properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=0"))
        self.assertTrue(greps(data, "SubState=dead"))
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=disabled"))
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=0"))
        self.assertTrue(greps(data, "SubState=dead"))
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=enabled")) # <<<
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "Id=zzs.service"))
        self.assertTrue(greps(data, "Names=zzs.service"))
        self.assertTrue(greps(data, "Description=Testing"))
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertTrue(greps(data, "SubState=running")) # <<<
        self.assertTrue(greps(data, "ActiveState=active")) # <<<<
        self.assertTrue(greps(data, "LoadState=loaded"))
        self.assertTrue(greps(data, "UnitFileState=enabled")) 
        self.assertEqual(end, 0)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3302_service_config_show_single_properties(self):
        """ check that a named service config can show a single properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=active"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service -vv -p 'MainPID'"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3303_service_config_show_single_properties_plus_unknown(self):
        """ check that a named service config can show a single properties"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} show zzs.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=inactive"))
        self.assertEqual(len(data), 1)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} show zzs.service other.service -vv -p ActiveState"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "ActiveState=active"))
        self.assertEqual(len(data), 1)
        #
        cmd = "{systemctl} show zzs.service other.service -vv -p 'MainPID'"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "MainPID=[123456789][1234567890]*")) # <<<<
        self.assertEqual(len(data), 1)
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3401_service_status_show(self):
        """ check that a named service config can show its status"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} status zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: inactive"))
        self.assertTrue(greps(data, "[(]dead[)]"))
        self.assertTrue(greps(data, "disabled[)]"))
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} status zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: active"))
        self.assertTrue(greps(data, "[(]running[)]"))
        self.assertTrue(greps(data, "enabled[)]"))
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3403_service_status_show_plus_unknown(self):
        """ check that a named service config can show its status"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzs.service"),"""
            [Unit]
            Description=Testing S
            After=foo.service
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleep} 40
            ExecStop=/usr/bin/killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzs.service"), os_path(root, "/etc/systemd/system/zzs.service"))
        #
        cmd = "{systemctl} status zzs.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: inactive"))
        self.assertTrue(greps(data, "[(]dead[)]"))
        self.assertTrue(greps(data, "disabled[)]"))
        #
        cmd = "{systemctl} enable zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzs.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} status zzs.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        data = lines(out)
        self.assertTrue(greps(data, "zzs.service - Testing"))
        self.assertTrue(greps(data, "Loaded: loaded"))
        self.assertTrue(greps(data, "Active: active"))
        self.assertTrue(greps(data, "[(]running[)]"))
        self.assertTrue(greps(data, "enabled[)]"))
        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_3530_systemctl_py_default_workingdirectory_is_root(self):
        """ check that services without WorkingDirectory start in / """
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart={bindir}/zzz.sh
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertIn(root, log) # <<<<<<<<<< CHECK
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3531_systemctl_py_simple_in_workingdirectory(self):
        """ check that we can start simple services with a WorkingDirectory"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory={workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        os.makedirs(os_path(root, workingdir))
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3532_systemctl_py_with_bad_workingdirectory(self):
        """ check that we can start simple services with a bad WorkingDirectory"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory={workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        # os.makedirs(os_path(root, workingdir)) <<<
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertNotIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        self.assertIn(root, log)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_3533_systemctl_py_with_bad_workingdirectory(self):
        """ check that we can start simple services with a bad WorkingDirectory with '-'"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        logfile = os_path(root, "/var/log/test.log")
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        workingdir = "/var/testsleep"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            WorkingDirectory=-{workingdir}
            ExecStart={bindir}/zzz.sh
            ExecStop=killall {testsleep}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "zzz.sh"),"""
            #! /bin/sh
            log={logfile}
            date > "$log"
            pwd >> "$log"
            exec {bindir}/{testsleep} 50
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "zzz.sh"), os_path(root, "/usr/bin/zzz.sh"))
        # os.makedirs(os_path(root, workingdir)) <<<
        #
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertNotIn(os_path(root,workingdir), log) # <<<<<<<<<< CHECK
        self.assertIn(root, log)
        #
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        # self.rm_testdir()
        self.coverage()
    def test_4030_simple_service_functions(self):
        """ check that we manage simple services in a root env
            with commands like start, restart, stop, etc"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testscript = self.testname("testscript.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStartPre=echo %n
            ExecStart={bindir}/{testscript} 50
            ExecStartPost=echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=echo stopped $MAINPID
            ExecStopPost=sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscript),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            date +%T,starting >> {logfile}
            {bindir}/{testsleep} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertTrue(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertTrue(greps(log, "enter"))
        self.assertTrue(greps(log, "starting"))
        self.assertFalse(greps(log, "reload"))
        os.remove(logfile)
        #
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        # inspect the service's log
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        self.assertFalse(greps(log, "enter"))
        self.assertFalse(greps(log, "leave"))
        self.assertFalse(greps(log, "starting"))
        self.assertFalse(greps(log, "stopped"))
        self.assertTrue(greps(log, "reload"))
        os.remove(logfile)
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # no PID known so 'kill $MAINPID' fails
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will NOT restart an is-active service (with ExecReload)")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process (if ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])

        #
        # cleanup
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4032_forking_service_functions(self):
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4035_notify_service_functions(self):
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,args
            {end}
            stop() {begin}
                killall {testsleep}
            {end}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecStop={root}/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        #
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4036_notify_service_functions_with_reload(self):
        """ check that we manage notify services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart. (with ExecReload)"""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        self.skipTest("unfinished (bad functionality?)") # TODO
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
                ls -l  $NOTIFY_SOCKET
                {bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo "MAINPID=$!" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                echo "READY=1" | socat -v -d - UNIX-CLIENT:$NOTIFY_SOCKET
                wait %1
                # ps -o pid,ppid,args
            {end}
            stop() {begin}
                killall {testsleep}
            {end}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            # PIDFile={root}/var/run/zzz.init.pid
            ExecStart={root}/usr/bin/zzz.init start
            ExecReload={root}/usr/bin/zzz.init reload
            ExecStop={root}/usr/bin/zzz.init stop
            TimeoutRestartSec=4
            TimeoutReloadSec=4
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))

        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active (if no ExecReload)")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top4 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps4 = find_pids(top4, testsleep)
        logg.info("found PIDs %s and %s", ps3, ps4)
        self.assertTrue(len(ps3), 1)
        self.assertTrue(len(ps4), 1)
        self.assertNotEqual(ps3[0], ps4[0])
        #
        logg.info("== 'kill' will bring is-active non-active as well (when the PID is known)")        
        cmd = "{systemctl} kill zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "failed")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("-- and we check that there is a new PID for the service process (if no ExecReload)")
        ps5 = find_pids(top5, testsleep)
        ps6 = find_pids(top6, testsleep)
        logg.info("found PIDs %s and %s", ps5, ps6)
        self.assertTrue(len(ps5), 1)
        self.assertTrue(len(ps6), 1)
        self.assertNotEqual(ps5[0], ps6[0])
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.rm_testdir()
        self.coverage()
    def test_4037_oneshot_service_functions(self):
        """ check that we manage oneshot services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/usr/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/usr/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "backup"), os_path(root, "/usr/bin/backup"))
        text_file(os_path(root, "/var/tmp/test.0"), """..""")
        is_active = "{systemctl} is-active zzz.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active")
        self.assertEqual(end, 0)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4038_oneshot_and_unknown_service_functions(self):
        """ check that we manage multiple services even when some
            services are not actually known. Along with oneshot serivce
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart / we have only different exit-code."""
        if not os.path.exists("/usr/bin/socat"):
            self.skipTest("missing /usr/bin/socat")
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=oneshot
            ExecStartPre={bindir}/backup {root}/var/tmp/test.1 {root}/var/tmp/test.2
            ExecStart=/usr/bin/touch {root}/var/tmp/test.1
            ExecStop=/usr/bin/rm {root}/var/tmp/test.1
            ExecStopPost=/usr/bin/rm -f {root}/var/tmp/test.2
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "backup"), """
           #! /bin/sh
           set -x
           test ! -f "$1" || mv -v "$1" "$2"
        """)
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        copy_tool(os_path(testdir, "backup"), os_path(root, "/usr/bin/backup"))
        text_file(os_path(root, "/var/tmp/test.0"), """..""")
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        is_active = "{systemctl} is-active zzz.service other.service -vv"
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1) 
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "active\nunknown")
        self.assertEqual(end, 1)
        self.assertTrue(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("== 'stop' will brings it back to 'inactive'")        
        cmd = "{systemctl} stop zzz.service other.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info("%s =>\n%s", cmd, out)
        self.assertNotEqual(end, 0)
        act, end = output2(is_active.format(**locals()))
        self.assertEqual(act.strip(), "inactive\nunknown")
        self.assertEqual(end, 1)
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.1")))
        self.assertFalse(os.path.exists(os_path(root, "/var/tmp/test.2")))
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()
    def test_4039_sysv_service_functions(self):
        """ check that we manage SysV services in a root env
            with basic run-service commands: start, stop, restart,
            reload, try-restart, reload-or-restart, kill and
            reload-or-try-restart."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            ### BEGIN INIT INFO
            # Required-Start: $local_fs $remote_fs $syslog $network 
            # Required-Stop:  $local_fs $remote_fs $syslog $network
            # Default-Start:  3 5
            # Default-Stop:   0 1 2 6
            # Short-Description: Testing Z
            # Description:    Allows for SysV testing
            ### END INIT INFO
            logfile={logfile}
            sleeptime=50
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} $sleeptime 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
               cat "RUNNING `cat {root}/var/run/zzz.init.pid`"
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
            case "$1" in start)
               date "+START.%T" >> $logfile
               start >> $logfile 2>&1
               date "+start.%T" >> $logfile
            ;; stop)
               date "+STOP.%T" >> $logfile
               stop >> $logfile 2>&1
               date "+stop.%T" >> $logfile
            ;; restart)
               date "+RESTART.%T" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               date "+.%T" >> $logfile
            ;; reload)
               date "+RELOAD.%T" >> $logfile
               echo "...." >> $logfile 2>&1
               date "+reload.%T" >> $logfile
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/etc/init.d/zzz"))

        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'restart' shall start a service that NOT is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top1= top
        #
        logg.info("== 'restart' shall restart a service that is-active")        
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top2 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        def find_pids(ps_output, command):
            pids = []
            for line in ps_output.split("\n"):
                if command not in line: continue
                m = re.match(r"\s*[\d:]*\s+(\S+)\s+(\S+)\s+(.*)", line)
                pid, ppid, args = m.groups()
                # logg.info("  %s | %s | %s", pid, ppid, args)
                pids.append(pid)
            return pids
        ps1 = find_pids(top1, testsleep)
        ps2 = find_pids(top2, testsleep)
        logg.info("found PIDs %s and %s", ps1, ps2)
        self.assertTrue(len(ps1), 1)
        self.assertTrue(len(ps2), 1)
        self.assertNotEqual(ps1[0], ps2[0])
        #
        logg.info("== 'reload' will NOT restart a service that is-active")        
        cmd = "{systemctl} reload zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top3 = top
        #
        logg.info("-- and we check that there is NO new PID for the service process")
        ps3 = find_pids(top3, testsleep)
        logg.info("found PIDs %s and %s", ps2, ps3)
        self.assertTrue(len(ps2), 1)
        self.assertTrue(len(ps3), 1)
        self.assertEqual(ps2[0], ps3[0])
        #
        logg.info("== 'reload-or-restart' may restart a service that is-active")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        logg.info("== 'stop' will turn 'failed' to 'inactive' (when the PID is known)")        
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-try-restart' will not start a not-active service")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'try-restart' will not start a not-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        logg.info("== 'reload-or-restart' will start a not-active service")        
        cmd = "{systemctl} reload-or-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top5 = top
        #
        logg.info("== 'reload-or-try-restart' will restart an is-active service (with no ExecReload)")        
        cmd = "{systemctl} reload-or-try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top6 = top
        #
        logg.info("== 'try-restart' will restart an is-active service")        
        cmd = "{systemctl} try-restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        top7 = top
        #
        logg.info("-- and we check that there is a new PID for the service process")
        ps6 = find_pids(top6, testsleep)
        ps7 = find_pids(top7, testsleep)
        logg.info("found PIDs %s and %s", ps6, ps7)
        self.assertTrue(len(ps6), 1)
        self.assertTrue(len(ps7), 1)
        self.assertNotEqual(ps6[0], ps7[0])
        #
        logg.info("LOG\n%s", " "+open(logfile).read().replace("\n","\n "))
        self.rm_testdir()
        self.coverage()

    def test_4050_forking_service_failed_functions(self):
        """ check that we manage forking services in a root env
            with basic run-service commands: start, stop, restart,
            checking the executions when some part fails."""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        logfile = os_path(root, "/var/log/"+testsleep+".log")
        bindir = os_path(root, "/usr/bin")
        fail = os_path(root, "/tmp/fail")
        os.makedirs(os_path(root, "/var/run"))
        text_file(logfile, "created\n")
        begin = "{" ; end = "}"
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            logfile={logfile}
            start() {begin} 
               [ -d /var/run ] || mkdir -p /var/run
               ({bindir}/{testsleep} 50 0<&- &>/dev/null &
                echo $! > {root}/var/run/zzz.init.pid
               ) &
               wait %1
               # ps -o pid,ppid,args
            {end}
            stop() {begin}
               killall {testsleep}
            {end}
            echo "run-$1" >> $logfile
            if test -f {fail}$1; then
               echo "fail-$1" >> $logfile
               exit 1
            fi
            case "$1" 
            in start)
               echo "START-IT" >> $logfile
               start >> $logfile 2>&1
               echo "started" >> $logfile
            ;; stop)
               echo "STOP-IT" >> $logfile
               stop >> $logfile 2>&1
               echo "stopped" >> $logfile
            ;; restart)
               echo "RESTART-IT" >> $logfile
               stop >> $logfile 2>&1
               start >> $logfile 2>&1
               echo "restarted" >> $logfile
            ;; reload)
               echo "RELOAD-IT" >> $logfile
               echo "...." >> $logfile 2>&1
               echo "reloaded" >> $logfile
            ;; start-pre)
               echo "START-PRE" >> $logfile
            ;; start-post)
               echo "START-POST" >> $logfile
            ;; stop-post)
               echo "STOP-POST" >> $logfile
            ;; esac 
            echo "done$1" >&2
            if test -f {fail}after$1; then
               echo "fail-after-$1" >> $logfile
               exit 1
            fi
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile={root}/var/run/zzz.init.pid
            ExecStartPre={root}/usr/bin/zzz.init start-pre
            ExecStart={root}/usr/bin/zzz.init start
            ExecStartPost={root}/usr/bin/zzz.init start-post
            ExecStop={root}/usr/bin/zzz.init stop
            ExecStopPost={root}/usr/bin/zzz.init stop-post
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "zzz.init"), os_path(root, "/usr/bin/zzz.init"))
        copy_file(os_path(testdir, "zzz.service"), os_path(root, "/etc/systemd/system/zzz.service"))
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, ["created"])
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST"])
        #
        logg.info("== 'stop' shall stop a service that is-active")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 1)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-stop", "STOP-IT", "stopped",
           "run-stop-post", "STOP-POST"])
        #
        text_file(fail+"start", "")
        #
        logg.info("== 'start' returns to stopped if the main call fails ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "fail-start",
           "run-stop-post", "STOP-POST"])
        #
        logg.info("== 'stop' on stopped service does not do much ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log[:2], [
           "run-stop", "STOP-IT" ])
        self.assertEqual(log[-2:], [
           "run-stop-post", "STOP-POST"])
        #
        logg.info("== 'restart' on a stopped item remains stopped if the main call fails ")
        cmd = "{systemctl} restart zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "fail-start",
           "run-stop-post", "STOP-POST"])
        #
        os.remove(fail+"start")
        text_file(fail+"stop", "")
        #
        logg.info("== 'start' that service ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' may have a failed item ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        # 'active' because the PIDFile process was not killed
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST",
           "run-stop", "fail-stop"])
        #
        os.remove(fail+"stop")
        text_file(fail+"afterstop", "")
        #
        logg.info("== 'start' that service ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        logg.info("== 'stop' may have a failed item ")
        cmd = "{systemctl} stop zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertEqual(out.strip(), "inactive")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started",
           "run-start-post", "START-POST",
           "run-stop", "STOP-IT", "stopped", "fail-after-stop",
           "run-stop-post", "STOP-POST"])
        #
        os.remove(fail+"afterstop")
        text_file(fail+"afterstart", "")
        #
        logg.info("== 'start' shall start a service that is NOT is-active ")
        cmd = "{systemctl} start zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} is-active zzz.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s \n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertEqual(out.strip(), "active")
        #
        log = lines(open(logfile))
        logg.info("LOG\n %s", "\n ".join(log))
        os.remove(logfile)
        self.assertEqual(log, [
           "run-start-pre", "START-PRE", 
           "run-start", "START-IT", "started", "fail-after-start",
           "run-start-post", "START-POST"])
        #
        self.rm_testdir()
        self.coverage()
    def test_4101_systemctl_py_kill_basic_behaviour(self):
        """ check systemctl_py kill basic behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepB} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepC} 50
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "killall {testsleepC}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # already down
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1) # nothing to kill
        #
        time.sleep(1)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        self.rm_testdir()
        self.coverage()
    def test_4105_systemctl_py_kill_in_stop(self):
        """ check systemctl_py kill from ExecStop"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("sleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        bindir = os_path(root, "/usr/bin")
        rundir = os_path(root, "/var/run")
        begin="{"
        end="}"
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepB} 40
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart={bindir}/{testsleepC} 50
            ExecStop=/usr/bin/kill ${begin}MAINPID{end}
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(rundir)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} stop zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        # self.assertEqual(end, 0)
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzb.service.pid"))
        self.assertTrue(greps(out, "zzc.service.pid"))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "zzb.service.pid"))
        self.assertTrue(greps(out, "zzc.service.pid")) # TODO ?
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "{systemctl} start zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        self.assertTrue(greps(top, testsleepC))
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "zzb.service.pid"))
        self.assertTrue(greps(out, "zzc.service.pid"))
        #
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        cmd = "killall {testsleepC}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # already down
        cmd = "{systemctl} kill zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 1) # nothing to kill
        #
        cmd = "ls -l {rundir}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "zzb.service.pid")) # issue #13
        self.assertTrue(greps(out, "zzc.service.pid")) # TODO ?
        #
        time.sleep(1)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        self.assertFalse(greps(top, testsleepC))
        #
        self.rm_testdir()
        self.coverage()
    def test_4120_systemctl_kill_ignore_behaviour(self):
        """ systemctl kill ignore behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        testscriptB = self.testname("testscriptB.sh")
        testscriptC = self.testname("testscriptC.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre=echo %n
            ExecStart={bindir}/{testscriptB} 50
            ExecStartPost=echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=echo stopped $MAINPID
            ExecStopPost=sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            # KillSignal=SIGQUIT
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscriptB),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            ignored () {begin}
              date +%T,ignored >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            trap "ignored" 15
            date +%T,starting >> {logfile}
            {bindir}/{testsleepB} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 15
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testscriptB))
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} kill zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testscriptB))
        self.assertTrue(greps(top, testsleepB)) # TODO: kill children as well (in default KillMode)
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertTrue(greps(log, "ignored"))
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleepB))
        #
        self.rm_testdir()
        self.coverage()
    def test_4121_systemctl_kill_ignore_nokill_behaviour(self):
        """ systemctl kill ignore and nokill behaviour"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        testsleep = self.testname("testsleep")
        testsleepB = testsleep+"B"
        testsleepC = testsleep+"C"
        testscriptB = self.testname("testscriptB.sh")
        testscriptC = self.testname("testscriptC.sh")
        logfile = os_path(root, "/var/log/test.log")
        bindir = os_path(root, "/usr/bin")
        begin = "{"
        end = "}"
        text_file(logfile, "")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre=echo %n
            ExecStart={bindir}/{testscriptB} 50
            ExecStartPost=echo started $MAINPID
            ExecStop=/usr/bin/kill -3 $MAINPID
            ExecStopPost=echo stopped $MAINPID
            ExecStopPost=sleep 2
            ExecReload=/usr/bin/kill -10 $MAINPID
            # KillSignal=SIGQUIT
            SendSIGKILL=no
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(bindir, testscriptB),"""
            #! /bin/sh
            date +%T,enter > {logfile}
            stops () {begin}
              date +%T,stopping >> {logfile}
              killall {testsleep}
              date +%T,stopped >> {logfile}
            {end}
            reload () {begin}
              date +%T,reloading >> {logfile}
              date +%T,reloaded >> {logfile}
            {end}
            ignored () {begin}
              date +%T,ignored >> {logfile}
            {end}
            trap "stops" 3
            trap "reload" 10
            trap "ignored" 15
            date +%T,starting >> {logfile}
            {bindir}/{testsleepB} $1 >> {logfile} 2>&1 &
            while kill -0 $!; do 
               # use 'kill -0' to check the existance of the child
               date +%T,waiting >> {logfile}
               # use 'wait' for children AND external signals
               wait
            done
            date +%T,leaving >> {logfile}
            trap - 3 10 15
            date +%T,leave >> {logfile}
        """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepB))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleepC))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        #
        cmd = "{systemctl} start zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} stop zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testscriptB))
        self.assertTrue(greps(top, testsleepB))
        #
        cmd = "{systemctl} kill zzb.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # not killed
        #
        time.sleep(1) # kill is asynchronous
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testscriptB)) # still alive
        self.assertTrue(greps(top, testsleepB)) 
        #
        log = lines(open(logfile).read())
        logg.info("LOG %s\n| %s", logfile, "\n| ".join(log))
        self.assertTrue(greps(log, "ignored"))
        #
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        cmd = "killall {testsleepB}"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        #
        time.sleep(1) # kill is asynchronous
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testscriptB))
        self.assertFalse(greps(top, testsleepB))
        #
        self.rm_testdir()
        self.coverage()

    def test_4201_systemctl_py_dependencies_plain_start_order(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps  = output(list_dependencies.format(**locals()))
        logg.info("deps \n%s", deps)
        #
        cmd = "{systemctl} start zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "start-A")
        self.assertEqual(log[1], "start-B")
        self.assertEqual(log[2], "start-C")
        os.remove(logfile)
        #
        cmd = "{systemctl} stop zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "stop-A")
        self.assertEqual(log[1], "stop-B")
        self.assertEqual(log[2], "stop-C")
        os.remove(logfile)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4211_systemctl_py_dependencies_basic_reorder(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps  = output(list_dependencies.format(**locals()))
        logg.info("deps \n%s", deps)
        #
        cmd = "{systemctl} start zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "start-B")
        self.assertEqual(log[1], "start-A")
        self.assertEqual(log[2], "start-C")
        os.remove(logfile)
        #
        cmd = "{systemctl} stop zza.service zzb.service zzc.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* '"
        top = output(top_recent.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, testsleep+" 40"))
        #
        # inspect logfile
        log = lines(open(logfile))
        logg.info("logs \n| %s", "\n| ".join(log))
        self.assertEqual(log[0], "stop-C")
        self.assertEqual(log[1], "stop-A")
        self.assertEqual(log[2], "stop-B")
        os.remove(logfile)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4301_systemctl_py_list_dependencies_with_after(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4302_systemctl_py_list_dependencies_with_wants(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Wants=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Wants=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Wants)")
        self.assertEqual(deps[1], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Wants)")
        self.assertEqual(deps[1], "zzc.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4303_systemctl_py_list_dependencies_with_requires(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Requires=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requires)")
        self.assertEqual(deps[1], "zza.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service\t(Requested)")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service --now"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service\t(Requires)")
        self.assertEqual(deps[1], "zzc.service\t(Requested)")
        self.assertEqual(len(deps), 2)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4401_systemctl_py_list_dependencies_with_after(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            After=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            After=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(len(deps), 1)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4402_systemctl_py_list_dependencies_with_wants(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Wants=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Wants=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(deps[1], "| zzb.service: wanted to start")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service:")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzc.service:")
        self.assertEqual(deps[1], "| zza.service: wanted to start")
        self.assertEqual(deps[2], "| | zzb.service: wanted to start")
        self.assertEqual(len(deps), 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4403_systemctl_py_list_dependencies_with_requires(self):
        """ check list-dependencies - standard order of starting
            units is simply the command line order"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        testsleep = self.testname("sleep")
        bindir = os_path(root, "/usr/bin")
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-A'
            ExecStart={bindir}/{testsleep} 30
            ExecStopPost={bindir}/logger 'stop-A'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-B'
            ExecStart={bindir}/{testsleep} 40
            ExecStopPost={bindir}/logger 'stop-B'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            Requires=zza.service
            [Service]
            Type=simple
            ExecStartPre={bindir}/logger 'start-C'
            ExecStart={bindir}/{testsleep} 50
            ExecStopPost={bindir}/logger 'stop-C'
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        shell_file(os_path(testdir, "logger"),"""
            #! /bin/sh
            echo "$@" >> {logfile}
            cat {logfile} | sed -e "s|^| : |"
            true
            """.format(**locals()))
        copy_tool("/usr/bin/sleep", os_path(bindir, testsleep))
        copy_tool(os_path(testdir, "logger"), os_path(bindir, "logger"))
        copy_file(os_path(testdir, "zza.service"), os_path(root, "/etc/systemd/system/zza.service"))
        copy_file(os_path(testdir, "zzb.service"), os_path(root, "/etc/systemd/system/zzb.service"))
        copy_file(os_path(testdir, "zzc.service"), os_path(root, "/etc/systemd/system/zzc.service"))
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        list_dependencies = "{systemctl} list-dependencies zza.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zza.service:")
        self.assertEqual(deps[1], "| zzb.service: required to start")
        self.assertEqual(len(deps), 2)
        #
        list_dependencies = "{systemctl} list-dependencies zzb.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzb.service:")
        self.assertEqual(len(deps), 1)
        #
        #
        list_dependencies = "{systemctl} list-dependencies zzc.service"
        deps_text  = output(list_dependencies.format(**locals()))
        # logg.info("deps \n%s", deps_text)
        #
        # inspect logfile
        deps = lines(deps_text)
        logg.info("deps \n| %s", "\n| ".join(deps))
        self.assertEqual(deps[0], "zzc.service:")
        self.assertEqual(deps[1], "| zza.service: required to start")
        self.assertEqual(deps[2], "| | zzb.service: required to start")
        self.assertEqual(len(deps), 3)
        #
        kill_testsleep = "killall {testsleep}"
        sx____(kill_testsleep.format(**locals()))
        self.rm_testdir()
        self.coverage()
    def test_4900_unreadable_files_can_be_handled(self):
        """ a file may exist but it is unreadable"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=simple
            ExecStart=/usr/bin/sleep 10
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        text_file(os_path(root, "/etc/systemd/system-preset/our.preset"),"""
            enable zza.service
            disable zzb.service""")
        os.makedirs(os_path(root, "/var/run"))
        os.makedirs(os_path(root, "/var/log"))
        #
        os.chmod(os_path(root, "/etc/systemd/system/zza.service"), 0222)
        #
        cmd = "{systemctl} start zza"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} start zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} stop zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} try-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload-or-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload-or-try-restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} kill zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        #
        cmd = "{systemctl} is-active zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        self.assertTrue(greps(out, "unknown"))
        cmd = "{systemctl} is-failed zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # made so
        self.assertTrue(greps(out, "unknown"))
        #
        cmd = "{systemctl} status zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertTrue(greps(out, "zza.service - NOT-FOUND"))
        #
        cmd = "{systemctl} show zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # shows not-found state ok
        self.assertTrue(greps(out, "LoadState=not-loaded"))
        #
        cmd = "{systemctl} cat zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.assertTrue(greps(out, "Unit zza.service is not-loaded"))
        #
        cmd = "{systemctl} list-dependencies zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # always succeeds
        #
        cmd = "{systemctl} enable zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} disable zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} is-enabled zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # ok
        #
        cmd = "{systemctl} preset zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        cmd = "{systemctl} preset-all"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) 
        #
        cmd = "{systemctl} daemon-reload"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # always succeeds
        #
        self.rm_testdir()
        self.coverage()
    def test_4901_unsupported_run_type_for_service(self):
        """ a service file may exist but the run type is not supported"""
        testname = self.testname()
        testdir = self.testdir()
        user = self.user()
        root = self.root(testdir)
        systemctl = _cov + _systemctl_py + " --root=" + root
        logfile = os_path(root, "/var/log/"+testname+".log")
        text_file(os_path(root, "/etc/systemd/system/zza.service"),"""
            [Unit]
            Description=Testing A
            Requires=zzb.service
            [Service]
            Type=foo
            ExecStart=/usr/bin/sleep 10
            ExecStop=/usr/bin/kill $MAINPID
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))
        #
        cmd = "{systemctl} start zza"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} start zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} stop zza.service -vv"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} reload zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "{systemctl} restart zza.service"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        self.rm_testdir()
        self.coverage()

    def test_5001_systemctl_py_inside_container(self):
        """ check that we can run systemctl.py inside a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        python = _python
        systemctl_py = _systemctl_py
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out, "systemctl.py"))
        #
        self.rm_testdir()
    def test_5002_systemctl_py_enable_in_container(self):
        """ check that we can enable services in a docker container """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl list-unit-files"
        # sh____(list_units_systemctl.format(**locals()))
        out = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out, "zza.service.*static"))
        self.assertTrue(greps(out, "zzb.service.*disabled"))
        self.assertTrue(greps(out, "zzc.service.*enabled"))
        #
        self.rm_testdir()
    def test_5003_systemctl_py_default_services_in_container(self):
        """ check that we can enable services in a docker container to have default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        list_units_systemctl = "docker exec {testname} systemctl default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out2 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out2)
        list_units_systemctl = "docker exec {testname} systemctl --all default-services -vv"
        # sh____(list_units_systemctl.format(**locals()))
        out3 = output(list_units_systemctl.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.assertTrue(greps(out2, "zzb.service"))
        self.assertTrue(greps(out2, "zzc.service"))
        self.assertEqual(len(lines(out2)), 2)
        self.assertTrue(greps(out3, "zzb.service"))
        self.assertTrue(greps(out3, "zzc.service"))
        # self.assertGreater(len(lines(out2)), 2)
        #
        self.rm_testdir()
    def test_5030_systemctl_py_start_simple(self):
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=testsleep 50
            ExecStop=killall testsleep
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5031_systemctl_py_start_extra_simple(self):
        """ check that we can start simple services in a container"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5032_systemctl_py_start_forking(self):
        """ check that we can start forking services in a container w/ PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               [ -d /var/run ] || mkdir -p /var/run
               (testsleep 50 0<&- &>/dev/null &
                echo $! > /var/run/zzz.init.pid
               ) &
               wait %1
               ps -o pid,ppid,args
            ;; stop)
               killall testsleep
            ;; esac 
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            PIDFile=/var/run/zzz.init.pid
            ExecStart=/usr/bin/zzz.init start
            ExceStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5033_systemctl_py_start_forking_without_pid_file(self):
        """ check that we can start forking services in a container without PIDFile"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               (testsleep 50 0<&- &>/dev/null &) &
               wait %1
               ps -o pid,ppid,args >&2
            ;; stop)
               killall testsleep
               echo killed all testsleep >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0""")
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vv"
        sx____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5035_systemctl_py_start_notify_by_timeout(self):
        """ check that we can start simple services in a container w/ notify timeout"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        shell_file(os_path(testdir, "killall"),"""
            #! /bin/sh
            ps -eo pid,comm | { while read pid comm; do
               if [ "$comm" = "$1" ]; then
                  echo kill $pid
                  kill $pid
               fi done } """)   
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=notify
            ExecStart=testsleep 50
            ExceStop=killall testsleep
            TimeoutSec=4
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/killall {testname}:/usr/bin/killall"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out)
        self.assertTrue(greps(out, "zzz.service"))
        self.assertEqual(len(lines(out)), 1)
        #
        cmd = "docker exec {testname} systemctl start zzz.service -vvvv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep"))
        #
        cmd = "docker exec {testname} systemctl stop zzz.service -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5100_systemctl_py_run_default_services_in_container(self):
        """ check that we can enable services in a docker container to be run as default-services"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -vv"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        cmd = "docker exec {testname} systemctl default -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5120_systemctl_py_run_default_services_from_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"--init\",\"default\",\"-vv\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5130_systemctl_py_run_default_services_from_simple_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD \"/usr/bin/systemctl\"'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5133_systemctl_py_run_default_services_from_single_service_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= CENTOS
        systemctl_py = _systemctl_py
        images = IMAGES
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_6000_precheck_coverage_install(self):
        """ Allow to have a coverage tool be installed."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
            ## https://github.com/openSUSE/docker-containers/issues/64
            #cmd = "docker exec {testname} {package} rr oss-update"
            #sh____(cmd.format(**locals()))
            #cmd = "docker exec {testname} {package} ar -f http://download.opensuse.org/update/leap/42.3/oss/openSUSE:Leap:42.3:Update.repo"
            #sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} {package} install -y {python_coverage}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_6130_systemctl_py_run_default_services_from_simple_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD \"/usr/bin/systemctl\"'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker exec {testname} systemctl halt -vvvv"
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6133_systemctl_py_run_default_services_from_single_service_saved_container(self):
        """ check that we can enable services in a docker container to be run as default-services
            after it has been restarted from a commit-saved container image.
            This includes some corage on the init-services."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zza.service"),"""
            [Unit]
            Description=Testing A""")
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zza.service {testname}:/etc/systemd/system/zza.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"zzc.service\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        #
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40")) # <<<<<<<<<< difference to 5033
        self.assertTrue(greps(top, "testsleep 50"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            okay_coverage = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(okay_coverage.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6200_systemctl_py_switch_users_is_possible(self):
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=user1
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=user1
            Group=group2
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=group2
            ExecStart=testsleep 60
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 150"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "docker exec {testname} touch /.coverage"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} chmod 777 /.coverage"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzb.service -v"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzc.service -v"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start zzd.service -v"
        sh____(cmd.format(**locals()))
        #
        # first of all, it starts commands like the service specs without user/group
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        # but really it has some user/group changed
        top_container = "docker exec {testname} ps -eo user,group,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "user1 .*root .*testsleep 40"))
        self.assertTrue(greps(top, "user1 .*group2 .*testsleep 50"))
        self.assertTrue(greps(top, "root .*group2 .*testsleep 60"))
        # and the pid file has changed as well
        cmd = "docker exec {testname} ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "user1 .*root .*zzb.service.pid"))
        cmd = "docker exec {testname} ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "user1 .*group2 .*zzc.service.pid"))
        cmd = "docker exec {testname} ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "root .*group2 .*zzd.service.pid"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6201_systemctl_py_switch_users_is_possible_from_saved_container(self):
        """ check that we can put setuid/setgid definitions in a service
            specfile which also works on the pid file itself """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        text_file(os_path(testdir, "zzb.service"),"""
            [Unit]
            Description=Testing B
            [Service]
            Type=simple
            User=user1
            ExecStart=testsleep 40
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzc.service"),"""
            [Unit]
            Description=Testing C
            [Service]
            Type=simple
            User=user1
            Group=group2
            ExecStart=testsleep 50
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zzd.service"),"""
            [Unit]
            Description=Testing D
            [Service]
            Type=simple
            Group=group2
            ExecStart=testsleep 60
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzb.service {testname}:/etc/systemd/system/zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzc.service {testname}:/etc/systemd/system/zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzd.service {testname}:/etc/systemd/system/zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzb.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzc.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzd.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        # sh____(cmd.format(**locals()))
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        # .........................................vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(5)
        #
        # first of all, it starts commands like the service specs without user/group
        top_container2 = "docker exec {testname}x ps -eo pid,ppid,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "testsleep 40"))
        self.assertTrue(greps(top, "testsleep 50"))
        self.assertTrue(greps(top, "testsleep 60"))
        # but really it has some user/group changed
        top_container2 = "docker exec {testname}x ps -eo user,group,args"
        top = output(top_container2.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "user1 .*root .*testsleep 40"))
        self.assertTrue(greps(top, "user1 .*group2 .*testsleep 50"))
        self.assertTrue(greps(top, "root .*group2 .*testsleep 60"))
        # and the pid file has changed as well
        cmd = "docker exec {testname}x ls -l /var/run/zzb.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "user1 .*root .*zzb.service.pid"))
        cmd = "docker exec {testname}x ls -l /var/run/zzc.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "user1 .*group2 .*zzc.service.pid"))
        cmd = "docker exec {testname}x ls -l /var/run/zzd.service.pid"
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out, "root .*group2 .*zzd.service.pid"))
        #
        cmd = "docker stop {testname}x" # <<<
        # sh____(cmd.format(**locals()))
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "testsleep 40"))
        self.assertFalse(greps(top, "testsleep 50"))
        self.assertFalse(greps(top, "testsleep 60"))
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6210_switch_users_and_workingdir_coverage(self):
        """ check that we can put workingdir and setuid/setgid definitions in a service
            and code parts for that are actually executed (test case without fork before) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        python_coverage = _python_coverage
        package = "yum"
        if greps(open("/etc/issue"), "openSUSE"):
           image = self.local_image(OPENSUSE)
           package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        systemctl_sh = os_path(testdir, "systemctl.sh")
        testsleep_sh = os_path(testdir, "testsleep.sh")
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        shell_file(testsleep_sh,"""
            #! /bin/sh
            logfile="/tmp/testsleep-$1.log"
            date > $logfile
            echo "pwd": `pwd` >> $logfile
            echo "user:" `id -un` >> $logfile
            echo "group:" `id -gn` >> $logfile
            testsleep $1
            """.format(**locals()))
        text_file(os_path(testdir, "zz4.service"),"""
            [Unit]
            Description=Testing 4
            [Service]
            Type=simple
            User=user1
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 4
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz5.service"),"""
            [Unit]
            Description=Testing 5
            [Service]
            Type=simple
            User=user1
            Group=group2
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 5
            [Install]
            WantedBy=multi-user.target""")
        text_file(os_path(testdir, "zz6.service"),"""
            [Unit]
            Description=Testing 6
            [Service]
            Type=simple
            Group=group2
            WorkingDirectory=/srv
            ExecStart=/usr/bin/testsleep.sh 6
            [Install]
            WantedBy=multi-user.target""")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/testsleep"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testsleep_sh} {testname}:/usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} chmod 755 /usr/bin/testsleep.sh"
        sh____(cmd.format(**locals()))
        if package == "zypper":
            cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
            sh____(cmd.format(**locals()))
        if COVERAGE:
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        else:
            cmd = "docker exec {testname} bash -c 'ls -l /usr/bin/python || {package} install -y python'"
            sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        if COVERAGE:
            cmd = "docker exec {testname} touch /.coverage"
            sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} chmod 777 /.coverage"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname} groupadd group2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} useradd user1 -g group2"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz4.service {testname}:/etc/systemd/system/zz4.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz5.service {testname}:/etc/systemd/system/zz5.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zz6.service {testname}:/etc/systemd/system/zz6.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz4.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.4"
        sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz5.service -vv"
        sh____(cmd.format(**locals())) 
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.5"
        sx____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl __exec_start_unit zz6.service -vv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} cp .coverage .coverage.{testname}.6"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker cp {testname}:/tmp/testsleep-4.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/tmp/testsleep-5.log {testdir}/"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/tmp/testsleep-6.log {testdir}/"
        sh____(cmd.format(**locals()))
        log4 = lines(open(os_path(testdir, "testsleep-4.log")))
        log5 = lines(open(os_path(testdir, "testsleep-5.log")))
        log6 = lines(open(os_path(testdir, "testsleep-6.log")))
        logg.info("testsleep-4.log\n %s", "\n ".join(log4))
        logg.info("testsleep-5.log\n %s", "\n ".join(log5))
        logg.info("testsleep-6.log\n %s", "\n ".join(log6))
        self.assertTrue(greps(log4, "pwd: /srv"))
        self.assertTrue(greps(log5, "pwd: /srv"))
        self.assertTrue(greps(log6, "pwd: /srv"))
        self.assertTrue(greps(log4, "group: root"))
        self.assertTrue(greps(log4, "user: user1"))
        self.assertTrue(greps(log5, "user: user1"))
        self.assertTrue(greps(log5, "group: group2"))
        self.assertTrue(greps(log6, "group: group2"))
        self.assertTrue(greps(log6, "user: root"))
        #
        if COVERAGE:
            cmd = "docker cp {testname}:/.coverage.{testname}.4 ."
            sh____(cmd.format(**locals()))
            cmd = "docker cp {testname}:/.coverage.{testname}.5 ."
            sh____(cmd.format(**locals()))
            cmd = "docker cp {testname}:/.coverage.{testname}.6 ."
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.4"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.5"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' .coverage.{testname}.6"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6600_systemctl_py_can_reap_zombies_in_a_container(self):
        """ check that we can reap zombies in a container managed by systemctl.py"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        testdir = self.testdir()
        images = IMAGES
        image = self.local_image(CENTOS)
        package = "yum"
        python_coverage = _python_coverage
        cov_run = ""
        if COVERAGE:
            cov_run = _cov_run
            if greps(open("/etc/issue"), "openSUSE"):
                image = self.local_image(OPENSUSE)
                package = "zypper"
        systemctl_py = os.path.realpath(_systemctl_py)
        systemctl_sh = os_path(testdir, "systemctl.sh")
        systemctl_py_run = systemctl_py.replace("/","_")[1:]
        shell_file(systemctl_sh,"""
            #! /bin/sh
            exec {cov_run} /{systemctl_py_run} "$@" -vv
            """.format(**locals()))
        user = self.user()
        testsleep = self.testname("sleep")
        shell_file(os_path(testdir, "zzz.init"), """
            #! /bin/bash
            case "$1" in start) 
               (/usr/bin/{testsleep} 50 0<&- &>/dev/null &) &
               wait %1
               # ps -o pid,ppid,args >&2
            ;; stop)
               killall {testsleep}
               echo killed all {testsleep} >&2
               sleep 1
            ;; esac 
            echo "done$1" >&2
            exit 0
            """.format(**locals()))
        text_file(os_path(testdir, "zzz.service"),"""
            [Unit]
            Description=Testing Z
            [Service]
            Type=forking
            ExecStart=/usr/bin/zzz.init start
            ExecStop=/usr/bin/zzz.init stop
            [Install]
            WantedBy=multi-user.target
            """.format(**locals()))


        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/{systemctl_py_run}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_sh} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker cp /usr/bin/sleep {testname}:/usr/bin/{testsleep}"
        sh____(cmd.format(**locals()))
        if COVERAGE:
            if package == "zypper":
                cmd = "docker exec {testname} {package} mr --no-gpgcheck oss-update"
                sh____(cmd.format(**locals()))
            cmd = "docker exec {testname} {package} install -y {python_coverage}"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker cp {testdir}/zzz.service {testname}:/etc/systemd/system/zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testdir}/zzz.init {testname}:/usr/bin/zzz.init"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable zzz.service"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl default-services -v"
        out2 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out2)
        #
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname}x {images}:{testname}"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # testsleep is running with parent-pid of '1'
        self.assertTrue(greps(top, " 1 /usr/bin/.*sleep 50"))
        # and the pid '1' is systemctl (actually systemctl.py)
        self.assertTrue(greps(top, " 1 .* 0 .*systemctl"))
        # and let's check no zombies around so far:
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< no zombie yet
        #
        # check the subprocess
        m = re.search(r"(?m)^(\S+)\s+(\d+)\s+(\d+)\s+(\S+.*sleep 50.*)$", top)
        if m:
            state, pid, ppid, args = m.groups()
        logg.info(" - sleep state = %s", state)
        logg.info(" - sleep pid = %s", pid)
        logg.info(" - sleep ppid = %s", ppid)
        logg.info(" - sleep args = %s", args)
        self.assertEqual(state, "S")
        self.assertEqual(ppid, "1")
        self.assertIn("sleep", args)
        #
        # and kill the subprocess
        cmd = "docker exec {testname}x kill {pid}"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "Z .*sleep.*<defunct>")) # <<< we have zombie!
        time.sleep(4)
        #
        cmd = "docker exec {testname}x ps -eo state,pid,ppid,args"
        top = output(cmd.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "Z .*sleep.*<defunct>")) # <<< and it's gone!
        time.sleep(1)
        #
        cmd = "docker stop {testname}x"
        out3 = output(cmd.format(**locals()))
        logg.info("\n>\n%s", out3)
        #
        if COVERAGE:
            coverage_file = ".coverage." + testname
            cmd = "docker cp {testname}x:.coverage {coverage_file}"
            sh____(cmd.format(**locals()))
            cmd = "sed -i -e 's:/{systemctl_py_run}:{systemctl_py}:' {coverage_file}"
            sh____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}x"
        sx____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_7001_centos_httpd_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        port=self.testport()
        name="centos-httpd"
        dockerfile="centos-httpd.dockerfile"
        images = IMAGES
        # WHEN
        cmd = "docker build . -f tests/{dockerfile} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {port}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{port}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7002_centos_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        port=self.testport()
        name="centos-postgres"
        dockerfile="centos-postgres.dockerfile"
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "docker build . -f tests/{dockerfile} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {port}:5432 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        login = "export PGUSER=testuser_11; export PGPASSWORD=Testuser.11"
        query = "SELECT rolname FROM pg_roles"
        cmd = "sleep 5; {login}; {psql} -p {port} -h 127.0.0.1 -d postgres -c '{query}' > {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7011_centos_httpd_socket_notify(self):
        """ WHEN using an image for a systemd-enabled CentOS 7, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            and in the systemctl.debug.log we can see NOTIFY_SOCKET
            messages with Apache sending a READY and MAINPID value."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        ## commit_container = "docker commit -c 'CMD [\"/usr/bin/systemctl\",\"init\",\"-vv\"]'  {testname} {images}:{testname}"
        ## sh____(commit_container.format(**locals()))
        ## stop_container = "docker rm --force {testname}"
        ## sx____(stop_container.format(**locals()))
        ## start_container = "docker run --detach --name {testname} {images}:{testname} sleep 200"
        ## sh____(start_container.format(**locals()))
        ## time.sleep(3)
        #
        container = self.ip_container(testname)
        cmd = "docker exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        # CHECK
        self.assertEqual(len(greps(open(testdir+"/systemctl.debug.log"), " ERROR ")), 0)
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "use NOTIFY_SOCKET="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "read_notify.*READY=1.*MAINPID="))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "notify start done"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "stop '/bin/kill' '-WINCH'"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "wait [$]NOTIFY_SOCKET"))
        self.assertTrue(greps(open(testdir+"/systemctl.debug.log"), "(dead)"))
        self.rm_testdir()
    def test_7012_centos_elasticsearch(self):
        """ WHEN we can setup a specific ElasticSearch version 
                 as being downloaded from the company.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see the ok-status from elastic."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        base_url = "https://download.elastic.co/elasticsearch/elasticsearch"
        filename = "elasticsearch-1.7.3.noarch.rpm"
        into_dir = "Software/ElasticSearch"
        download(base_url, filename, into_dir)
        self.assertTrue(greps(os.listdir("Software/ElasticSearch"), filename))
        #
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y java" # required
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y which" # TODO: missing requirement of elasticsearch
        sh____(cmd.format(**locals()))
        cmd = "docker cp Software/ElasticSearch {testname}:/srv/"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'yum install -y /srv/ElasticSearch/*.rpm'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable elasticsearch"
        sh____(cmd.format(**locals()))
        #
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name {testname} {images}:{testname} sleep 200"
        sh____(cmd.format(**locals()))
        time.sleep(3)
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "docker exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        testdir = self.testdir(testname)
        cmd = "sleep 5; wget -O {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir+"/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple start done PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID .*elasticsearch.service"))
        self.assertTrue(greps(systemctl_log, "stopped PID .* EXIT 143"))
        #
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_7013_centos_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php on CentOs"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y epel-release"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum repolist"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin"
        sh____(cmd.format(**locals()))
        #
        WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
        INC_CONF="/etc/phpMyAdmin/config.inc.php"
        INDEX_PHP="/var/www/html/index.php"
        cmd = "docker exec {testname} bash -c 'echo \"<?php phpinfo(); ?>\" > {INDEX_PHP}'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' {WEB_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start mariadb -vvv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} mysqladmin -uroot password 'N0.secret'"
        sh____(cmd.format(**locals()))
        text_file(os_path(testdir,"testuser.sql"), "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'")
        cmd = "docker cp {testdir}/testuser.sql {testname}:/srv/testuser.sql" 
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'cat /srv/testuser.sql | mysql -uroot -pN0.secret'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i -e \"/'user'/s|=.*;|='testuser_OK';|\" {INC_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i -e \"/'password'/s|=.*;|='Testuser.OK';|\" {INC_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        #
        self.rm_testdir()
    def test_7014_opensuse_lamp_stack(self):
        """ Check setup of Linux/Mariadb/Apache/Php" on Opensuse"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(OPENSUSE)
        python_base = os.path.basename(_python)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} zypper install -r oss -y {python_base}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} zypper install -r oss -y apache2 apache2-utils mariadb-server mariadb-tools php5 phpMyAdmin"
        sh____(cmd.format(**locals()))
        #
        WEB_CONF="/etc/apache2/conf.d/phpMyAdmin.conf"
        INC_CONF="/etc/phpMyAdmin/config.inc.php"
        INDEX_PHP="/srv/www/htdocs/index.php"
        cmd = "docker exec {testname} bash -c 'echo \"<?php phpinfo(); ?>\" > {INDEX_PHP}'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' {WEB_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start mysql -vvv"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} mysqladmin -uroot password 'N0.secret'"
        sh____(cmd.format(**locals()))
        text_file(os_path(testdir,"testuser.sql"), "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'")
        cmd = "docker cp {testdir}/testuser.sql {testname}:/srv/testuser.sql" 
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'cat /srv/testuser.sql | mysql -uroot -pN0.secret'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i -e \"/'user'/s|=.*;|='testuser_OK';|\" {INC_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} sed -i -e \"/'password'/s|=.*;|='Testuser.OK';|\" {INC_CONF}"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start apache2"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}/phpMyAdmin"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        #
        self.rm_testdir()
    def test_7020_ubuntu_apache2_with_saved_container(self):
        """ WHEN using a systemd enabled Ubuntu as the base image
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        testname = self.testname()
        port=self.testport()
        images = IMAGES
        image = "ubuntu:16.04"
        python_base = os.path.basename(_python)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, port, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get update"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} apt-get install -y apache2 {python_base}"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable apache2"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        # .........................................
        cmd = "docker commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run -d -p {port}:80 --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        # THEN
        tmp = self.testdir(testname)
        cmd = "sleep 5; wget -O {tmp}/{testname}.txt http://127.0.0.1:{port}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {tmp}/{testname}.txt"
        sh____(cmd.format(**locals()))
        # CLEAN
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    # @unittest.expectedFailure
    def test_8001_issue_1_start_mariadb_centos_7_0(self):
        """ issue 1: mariadb on centos 7.0 does not start"""
        # this was based on the expectation that "yum install mariadb" would allow
        # for a "systemctl start mysql" which in fact it doesn't. Double-checking
        # with "yum install mariadb-server" and "systemctl start mariadb" shows
        # that mariadb's unit file is buggy, because it does not specify a kill
        # signal that it's mysqld_safe controller does not ignore.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        # image= "centos:centos7.0.1406" # <<<< can not yum-install mariadb-server ?
        # image= "centos:centos7.1.1503"
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        # mariadb has a TimeoutSec=300 in the unit config:
        cmd = "docker run --detach --name={testname} {image} sleep 400"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y mariadb"
        sh____(cmd.format(**locals()))
        if False:
            # expected in bug report but that one can not work:
            cmd = "docker exec {testname} systemctl enable mysql"
            sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertFalse(greps(out,"mysqld"))
        #
        cmd = "docker exec {testname} yum install -y mariadb-server"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out,"mariadb.service"))
        #
        cmd = "docker exec {testname} systemctl start mariadb -vv"
        sh____(cmd.format(**locals()))
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "mysqld "))
        had_mysqld_safe = greps(top, "mysqld_safe ")
        #
        # NOTE: mariadb-5.5.52's mysqld_safe controller does ignore systemctl kill
        # but after a TimeoutSec=300 the 'systemctl kill' will send a SIGKILL to it
        # which leaves the mysqld to be still running -> this is an upstream error.
        cmd = "docker exec {testname} systemctl stop mariadb -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        # self.assertFalse(greps(top, "mysqld "))
        if greps(top, "mysqld ") and had_mysqld_safe:
            logg.critical("mysqld still running => this is an uptream error!")
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8002_issue_2_start_rsyslog_centos7(self):
        """ issue 2: rsyslog on centos 7 does not start"""
        # this was based on a ";Requires=xy" line in the unit file
        # but our unit parser did not regard ";" as starting a comment
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = self.testname()
        testdir = self.testdir()
        image= self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 50"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y rsyslog"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl --version"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl list-unit-files --type=service"
        sh____(cmd.format(**locals()))
        out = output(cmd.format(**locals()))
        self.assertTrue(greps(out,"rsyslog.service.*enabled"))
        #
        cmd = "docker exec {testname} systemctl start rsyslog -vv"
        sh____(cmd.format(**locals()))
        #
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertTrue(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = "docker exec {testname} systemctl stop rsyslog -vv"
        sh____(cmd.format(**locals()))
        top_container = "docker exec {testname} ps -eo pid,ppid,args"
        top = output(top_container.format(**locals()))
        logg.info("\n>>>\n%s", top)
        self.assertFalse(greps(top, "/usr/sbin/rsyslog"))
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8011_centos_httpd_socket_notify(self):
        """ start/restart behaviour if a httpd has failed - issue #11 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname=self.testname()
        testdir = self.testdir(testname)
        testport=self.testport()
        images = IMAGES
        image = self.local_image(CENTOS)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, testport, image)
        #
        cmd = "docker rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "docker run --detach --name={testname} {image} sleep 600"
        sh____(cmd.format(**locals()))
        cmd = "docker cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} yum install -y httpd httpd-tools"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl enable httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        cmd = "docker exec {testname} touch /var/log/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        sh____(cmd.format(**locals()))
        # THEN
        time.sleep(5)
        cmd = "wget -O {testdir}/result.txt http://{container}:80"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "docker exec {testname} systemctl status httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl stop httpd"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl status httpd"
        #
        # CRASH
        cmd = "docker exec {testname} bash -c 'cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.orig'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} bash -c 'echo foo > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl start httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # start failed
        cmd = "docker exec {testname} systemctl status httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0)
        cmd = "docker exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertNotEqual(end, 0) # restart failed
        #
        cmd = "docker exec {testname} bash -c 'cat /etc/httpd/conf/httpd.conf.orig > /etc/httpd/conf/httpd.conf'"
        sh____(cmd.format(**locals()))
        cmd = "docker exec {testname} systemctl restart httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # restart ok
        cmd = "docker exec {testname} systemctl stop httpd"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0) # down
        cmd = "docker exec {testname} systemctl status httpd"
        sx____(cmd.format(**locals()))
        #
        cmd = "docker cp {testname}:/var/log/systemctl.debug.log {testdir}/systemctl.debug.log"
        sh____(cmd.format(**locals()))
        cmd = "docker stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "docker rm --force {testname}"
        sh____(cmd.format(**locals()))
        #
        self.rm_testdir()
    def test_9000_ansible_test(self):
        """ FIXME: "-p testing_systemctl" makes containers like "testingsystemctl_<service>_1" ?! """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        sh____("ansible-playbook --version | grep ansible-playbook.2") # atleast version2
        new_image1 = "localhost:5000/testingsystemctl:serversystem"
        new_image2 = "localhost:5000/testingsystemctl:virtualdesktop"
        rmi_commit1 = 'docker rmi "{new_image1}"'
        rmi_commit2 = 'docker rmi "{new_image2}"'
        sx____(rmi_commit1.format(**locals()))
        sx____(rmi_commit2.format(**locals()))
        if False:
            self.test_9001_ansible_download_software()
            self.test_9002_ansible_restart_docker_build_compose()
            self.test_9003_ansible_run_build_step_playbooks()
            self.test_9004_ansible_save_build_step_as_new_images()
            self.test_9005_ansible_restart_docker_start_compose()
            self.test_9006_ansible_unlock_jenkins()
            self.test_9006_ansible_check_jenkins_login()
            self.test_9008_ansible_stop_all_containers()
    def test_9001_ansible_download_software(self):
        """ download the software parts (will be done just once) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        sh____("cd tests && ansible-playbook download-jenkins.yml -vv")
        sh____("cd tests && ansible-playbook download-selenium.yml -vv")
        sh____("cd tests && ansible-playbook download-firefox.yml -vv")
        # CHECK
        self.assertTrue(greps(os.listdir("Software/Jenkins"), "^jenkins.*[.]rpm"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-.*[.]tar.gz"))
        self.assertTrue(greps(os.listdir("Software/Selenium"), "^selenium-server.*[.]jar"))
        self.assertTrue(greps(os.listdir("Software/CentOS"), "^firefox.*[.]centos[.]x86_64[.]rpm"))
    def test_9002_ansible_restart_docker_build_compose(self):
        """ bring up the build-step deployment containers """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        drop_old_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml up -d"
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
    def test_9003_ansible_run_build_step_playbooks(self):
        """ run the build-playbook (using ansible roles) """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        testname = "test_9003"
        # WHEN environment is prepared
        make_files_dir = "test -d tests/files || mkdir tests/files"
        make_script_link = "cd tests/files && ln -sf ../../files/docker"
        sh____(make_files_dir)
        sh____(make_script_link)
        make_logfile_1 = "docker exec testingsystemctl1_serversystem_1 bash -c 'touch /var/log/systemctl.log'"
        make_logfile_2 = "docker exec testingsystemctl1_virtualdesktop_1 bash -c 'touch /var/log/systemctl.log'"
        sh____(make_logfile_1)
        sh____(make_logfile_2)
        # THEN ready to run the deployment playbook
        inventory = "tests/docker-build-compose.ini"
        playbooks = "tests/docker-build-playbook.yml"
        variables = "-e LOCAL=yes -e jenkins_prefix=/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # CLEAN
        drop_files_dir = "rm tests/files/docker"
        sh____(drop_files_dir)
        #
        # CHECK
        tmp = self.testdir(testname)
        read_logfile_1 = "docker cp testingsystemctl1_serversystem_1:/var/log/systemctl.log {tmp}/systemctl.server.log"
        read_logfile_2 = "docker cp testingsystemctl1_virtualdesktop_1:/var/log/systemctl.log {tmp}/systemctl.desktop.log"
        sh____(read_logfile_1.format(**locals()))
        sh____(read_logfile_2.format(**locals()))
        self.assertFalse(greps(open(tmp+"/systemctl.server.log"), " ERROR "))
        self.assertFalse(greps(open(tmp+"/systemctl.desktop.log"), " ERROR "))
        self.assertGreater(len(greps(open(tmp+"/systemctl.server.log"), " INFO ")), 10)
        self.assertGreater(len(greps(open(tmp+"/systemctl.desktop.log"), " INFO ")), 10)
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl daemon-reload"))
        # self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl status jenkins.service"))
        # self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "--property=ActiveState")) # <<< new
        self.assertTrue(greps(open(tmp+"/systemctl.server.log"), "/systemctl show jenkins.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl show xvnc.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl enable xvnc.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl enable selenium.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl is-enabled selenium.service"))
        self.assertTrue(greps(open(tmp+"/systemctl.desktop.log"), "/systemctl daemon-reload"))
    def test_9004_ansible_save_build_step_as_new_images(self):
        # stop the containers but keep them around
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        inventory = "tests/docker-build-compose.ini"
        playbooks = "tests/docker-build-stop.yml"
        variables = "-e LOCAL=yes"
        ansible = "ansible-playbook -i {inventory} {variables} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        message = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        startup = "CMD '/usr/bin/systemctl'"
        container1 = "testingsystemctl1_serversystem_1"
        new_image1 = "localhost:5000/testingsystemctl:serversystem"
        container2 = "testingsystemctl1_virtualdesktop_1"
        new_image2 = "localhost:5000/testingsystemctl:virtualdesktop"
        commit1 = 'docker commit -c "{startup}" -m "{message}" {container1} "{new_image1}"'
        commit2 = 'docker commit -c "{startup}" -m "{message}" {container2} "{new_image2}"'
        sh____(commit1.format(**locals()))
        sh____(commit2.format(**locals()))
        # CHECK
        self.assertTrue(greps(output("docker images"), IMAGES+".* serversystem "))
        self.assertTrue(greps(output("docker images"), IMAGES+".* virtualdesktop "))
    def test_9005_ansible_restart_docker_start_compose(self):
        """ bring up the start-step runtime containers from the new images"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        make_new_containers = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml up -d"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_containers}".format(**locals()))
        sh____("{make_new_containers} || {make_new_containers} || {make_new_containers}".format(**locals()))
        time.sleep(2) # sometimes the container dies early
        # CHECK
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl2_virtualdesktop_1$"))
        self.assertTrue(greps(output("docker ps"), " testingsystemctl2_serversystem_1$"))
    def test_9006_ansible_unlock_jenkins(self):
        """ unlock jenkins as a post-build config-example using selenium-server """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        inventory = "tests/docker-start-compose.ini"
        playbooks = "tests/docker-start-playbook.yml"
        variables = "-e LOCAL=yes -e j_username=installs -e j_password=installs.11"
        vartarget = "-e j_url=http://serversystem:8080/buildserver"
        ansible = "ansible-playbook -i {inventory} {variables} {vartarget} {playbooks} -vv"
        sh____(ansible.format(**locals()))
        # CHECK
        test_screenshot = "ls -l tests/*.png"
        sh____(test_screenshot)
    def test_9007_ansible_check_jenkins_login(self):
        """ check jenkins runs unlocked as a testcase result """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        tmp = self.testdir("test_9007")
        webtarget = "http://localhost:8080/buildserver/manage"
        weblogin = "--user installs --password installs.11 --auth-no-challenge"
        read_jenkins_html = "wget {weblogin} -O {tmp}/page.html {webtarget}"
        grep_jenkins_html = "grep 'Manage Nodes' {tmp}/page.html"
        sh____(read_jenkins_html.format(**locals()))
        sh____(grep_jenkins_html.format(**locals()))
    def test_9008_ansible_stop_all_containers(self):
        """ bring up the start-step runtime containers from the new images"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if _python.endswith("python3"): self.skipTest("no python3 on centos")
        time.sleep(3)
        drop_old_build_step = "docker-compose -p testingsystemctl1 -f tests/docker-build-compose.yml down"
        drop_old_start_step = "docker-compose -p testingsystemctl2 -f tests/docker-start-compose.yml down"
        sx____("{drop_old_build_step}".format(**locals()))
        sx____("{drop_old_start_step}".format(**locals()))
        # CHECK
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl1_serversystem_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl2_virtualdesktop_1$"))
        self.assertFalse(greps(output("docker ps"), " testingsystemctl2_serversystem_1$"))

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
       help="systemctl.py file to be tested (%default)")
    _o.add_option("-p","--python", metavar="EXE", default=_python,
       help="use another python execution engine [%default]")
    _o.add_option("-a","--coverage", action="count", default=0,
       help="gather coverage.py data (use -aa for new set) [%default]")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _python_version = output(_python + " --version 2>&1")
    if "Python 3" in _python_version:
        _cov_run = _cov3run
        _cov_cmd = _cov3cmd
        _python_coverage = _python3coverage
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
           os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
           os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    #
    if opt.coverage:
        COVERAGE = True
        _cov = _cov_run
        if opt.coverage > 1:
            if os.path.exists(".coverage"):
                logg.info("rm .coverage")
                os.remove(".coverage")
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = [ "test_*" ]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    if not logfile:
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
            Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            Runner(verbosity=opt.verbose).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
    if opt.coverage:
        print(" " + _cov_cmd + " combine")
        print(" " + _cov_cmd + " report " + _systemctl_py)
        print(" " + _cov_cmd + " annotate " + _systemctl_py)
