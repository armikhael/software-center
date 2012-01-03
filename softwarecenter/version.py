
import commands
VERSION='2.0.8-1canaima3'
CODENAME=commands.getoutput("lsb_release -s -c")
DISTRO=commands.getoutput("lsb_release -s -i")
RELEASE=commands.getoutput("lsb_release -s -r")
