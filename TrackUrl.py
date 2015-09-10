import sublime
import sublime_plugin
import urllib2

class HeadRequest(urllib2.Request):
  
  def get_method(self):
    return "HEAD"

class URLTracker():
  
  def __init__(self, url, view):
    self.view = view
    self.url = url
    self.last_updated = (0, 0, 0, 0, 0, 0, 0, 0, 0)
    filename = self.url.split("/")[-1]
    self.view.set_name("Tracker: #{0}".format(filename))
    
    edit = self.view.begin_edit()
    self.view.insert(edit, 0, "Fetching URL...")
    self.view.end_edit(edit)
    
    
  def is_dirty(self):
    response = urllib2.urlopen(HeadRequest(self.url))
    last_modified = response.info().getdate('Last-Modified')
    dirty = last_modified > self.last_updated
    self.last_updated = last_modified
    return dirty

  def check_for_update(self):
    if self.is_dirty():
      self.update_panel()

  def closed(self):
    return self.view.window() is None
  
  def update_panel(self):
    window = self.view.window()
    content = urllib2.urlopen(self.url).read()

    # Save what section is being looked at
    position = self.view.viewport_position()
    self.view.set_read_only(False)
    
    # Erase the contents of the panel and
    # replace with the new content
    edit = self.view.begin_edit()
    region = sublime.Region(0, self.view.size())
    self.view.erase(edit, region)
    self.view.insert(edit, 0, content)
    self.view.end_edit(edit)

    self.view.set_read_only(True)
    
    # Reset the view to where it was before
    self.view.set_viewport_position(position)

class TrackUrlCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    default = ""
    if len(self.view.sel()) > 0:
      default = self.view.substr(self.view.sel()[0])
    self.view.window().show_input_panel("Track URL:", default.strip(), self.init, None, None)
    pass

  def split_screen(self):
    window = self.view.window()
    
    #layout = window.get_layout()
    # http://www.sublimetext.com/forum/viewtopic.php?f=2&p=50358
    layout = {"cols": [0.0, 0.5, 1.0], "rows": [0.0, 1.0], "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]}
    window.set_layout(layout)

    # the group is which panel it's in, the new one is the last one I guess
    active_group = window.active_group()
    num_groups = len(layout['cells'])
    group_index = max(active_group, num_groups-1)
    tracking_view = window.new_file()
    tracking_view.set_scratch(True)
    window.set_view_index(tracking_view, group_index, 0)
    window.focus_group(active_group)
    return tracking_view
    
  def init(self, url):
    view = self.split_screen()
    tracker = URLTracker(url, view)

    if not hasattr(self, 'trackers'):
      self.trackers = []
    
    self.trackers.append(tracker)

    if not hasattr(self, 'checker_running'):
      self.check_updates()

  def check_updates(self):
    self.checker_running = True
    
    print id(self), "Looking at", len(self.trackers), "trackers"
    # Store the trackers that don't fail at updating
    self.trackers = [tracker for tracker in self.trackers if not tracker.closed()]
    for tracker in self.trackers:
      tracker.check_for_update()

    sublime.set_timeout(self.check_updates, 2000)