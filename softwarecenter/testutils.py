# Copyright (C) 2011 Canonical
#
# Authors:
#  Michael Vogt
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import os
import subprocess
import time

m_dbus = m_polkit = m_aptd = None
def start_dummy_backend():
    global m_dbus, m_polkit, m_aptd
    # start private dbus
    m_dbus = subprocess.Popen(["dbus-daemon", 
                               "--session", 
                               "--nofork",
                               "--print-address"], 
                              stdout=subprocess.PIPE)
    # get and store address
    bus_address = m_dbus.stdout.readline().strip()
    os.environ["SOFTWARE_CENTER_APTD_FAKE"] = bus_address
    # start fake polkit from python-aptdaemon.test
    env = { "DBUS_SESSION_BUS_ADDRESS" : bus_address,
          }
    m_polkit = subprocess.Popen(
        ["/usr/share/aptdaemon/tests/fake-polkitd.py", 
         "--allowed-actions=all"],
        env=env)
    # start aptd in dummy mode
    m_aptd = subprocess.Popen(
        ["/usr/sbin/aptd","--dummy", "--session-bus", "--disable-timeout"],
        env=env)
    # the sleep here is not ideal, but we need to wait a little bit
    # to ensure that the fake daemon and fake polkit is ready
    time.sleep(0.5)

def stop_dummy_backend():
    global m_dbus, m_polkit, m_aptd
    m_aptd.terminate()
    m_aptd.wait()
    m_polkit.terminate()
    m_polkit.wait()
    m_dbus.terminate()
    m_dbus.wait()

def get_test_gtk3_viewmanager():
    from gi.repository import Gtk
    from softwarecenter.ui.gtk3.session.viewmanager import (
        ViewManager, get_viewmanager)
    vm = get_viewmanager()
    if not vm:
        notebook = Gtk.Notebook()
        vm = ViewManager(notebook)
        vm.view_to_pane = {None : None}
    return vm

def get_test_db():
    from softwarecenter.db.database import StoreDatabase
    from softwarecenter.db.pkginfo import get_pkg_info
    import softwarecenter.paths
    cache = get_pkg_info()
    cache.open()
    db = StoreDatabase(softwarecenter.paths.XAPIAN_PATH, cache)
    db.open()
    return db

def get_test_install_backend():
    from softwarecenter.backend.installbackend import get_install_backend
    backend = get_install_backend()
    return backend

def get_test_gtk3_icon_cache():
    from softwarecenter.ui.gtk3.utils import get_sc_icon_theme
    import softwarecenter.paths
    icons = get_sc_icon_theme(softwarecenter.paths.datadir)
    return icons

def get_test_pkg_info():
    from softwarecenter.db.pkginfo import get_pkg_info
    cache = get_pkg_info()
    cache.open()
    return cache

def get_test_datadir():
    import softwarecenter.paths
    return softwarecenter.paths.datadir

def get_test_enquirer_matches(db, query=None, limit=20, sortmode=0):
    from softwarecenter.db.enquire import AppEnquire
    import xapian
    if query is None:
        query = xapian.Query("")
    enquirer = AppEnquire(db._aptcache, db)
    enquirer.set_query(query,
                       sortmode=sortmode,
                       limit=limit,
                       nonblocking_load=False)
    return enquirer.matches

def do_events():
    from gi.repository import GObject
    main_loop = GObject.main_context_default()
    while main_loop.pending():
        main_loop.iteration()

def get_mock_app_from_real_app(real_app):
    """ take a application and return a app where the details are a mock
        of the real details so they can easily be modified
    """
    from mock import Mock
    import copy
    app = copy.copy(real_app)
    db = get_test_db()
    details = app.get_details(db)
    details_mock = Mock()
    for a in dir(details):
        if a.startswith("_"): continue
        setattr(details_mock, a, getattr(details, a))
    app._details = details_mock
    app.get_details = lambda db: app._details
    return app
