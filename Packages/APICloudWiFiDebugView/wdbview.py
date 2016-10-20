import sublime, sublime_plugin
import logging, re
import threading
import traceback
import os, platform, time, sys
from os.path import join, getsize
import codecs

curDir = os.path.dirname(os.path.realpath(__file__))
print ('encoding value:', sys.getdefaultencoding())

# if sys.getdefaultencoding() != 'utf8':  
    # imp.reload(sys)  
    #sys.setdefaultencoding('utf8')  
################################################################################
#                             Utility functions                                #
################################################################################
def get_settings():
    return sublime.load_settings("WDBView.sublime-settings")

__wdb_settings_defaults = {
    "wdb_maxlines": 20000,
    "wdb_filter": ".",
    "wdb_auto_scroll": True,
    "wdb_snap_lines": 5
}


def __decode_wrap(dec):
    def __decode2(line):
        line = dec(line)
        try:
            # Only for Python2, in 3 str == unicode and the type unicode doesn't exist
            if not isinstance(line, unicode):
                line = line.decode("utf-8", "ignore")
        except UnicodeDecodeError as e:
            print("[WDBView] UnicodeDecodeError occurred:", e)
            print("[WDBView] the line is: ", [ord(c) for c in line])
        except:
            # Probably Python 3
            pass
        return line
    return __decode2

@__decode_wrap
def decode(ind):
    try:
        return ind.decode("utf-8")
    except:
        try:
            return ind.decode(sys.getdefaultencoding())
        except:
            return ind


wdb_views = []

wifi_log_file=''
if 'windows' in platform.system().lower():
    wifi_log_file=os.path.join('c:\\','APICloud','workspace','log_info')
else:
    wifi_log_file=os.path.join(curDir,'..','APICloudWiFiSync','tools','log_info')

 

################################################################################
#                WDBView class dealing with log_info file                   #
################################################################################
class WDBView(object):
    def __init__(self, name=""):
        self.__name = "WDB: %s" % name
        self.__fileSize = getsize(wifi_log_file)
        # self.__mtime = 0.0
        self.__view = None
        self.__last_fold = None
        self.__timer = None
        self.__lines = []
        self.__cond = threading.Condition()
        self.__maxlines = 20000
        self.__filter = re.compile(".")
        self.__do_scroll = True
        self.__manual_scroll = False
        self.__snapLines = 5
        self.__closing = False
        self.__view = sublime.active_window().new_file()
        self.__view.set_name(self.__name)
        self.__view.set_scratch(True)
        self.__view.set_read_only(True)
        self.__view.set_syntax_file("Packages/APICloudWiFiDebugView/wdb.tmLanguage")

        # print("running: %s" % cmd)
        
        threading.Thread(target=self.__output_thread).start()
        threading.Thread(target=self.__process_thread).start()

      # def close(self):
      #     if self.__adb_process != None and self.__adb_process.poll() == None:
      #         self.__adb_process.kill()

    def set_filter(self, filter):
        try:
            self.__filter = re.compile(filter)
            if self.__view:
                self.__last_fold = apply_filter(self.__view, self.__filter)
        except:
            traceback.print_exc()
            sublime.error_message("invalid regex")

    @property
    def name(self):
        return self.__name

    @property
    def device(self):
        return self.__device

    @property
    def view(self):
        return self.__view

    @property
    def filter(self):
        return self.__filter


    def __output_thread(self):
        while True:
            try:

                logging.info('wifi_log_file is '+wifi_log_file)
                print('wifi_log_file is '+wifi_log_file)

                if not os.path.exists(wifi_log_file):
                    sublime.status_message(u'请确认已经启动WiFi真机同步服务')
                    time.sleep(10)
                    continue
                else:
                    # statinfo = os.stat(wifi_log_file)
                    if self.__fileSize < getsize(wifi_log_file):
                        # 有新的log，将其打印到view中去
                        print('open log file')
                        #coding:utf-8
                        if 'windows' in platform.system().lower():
                            f = open(wifi_log_file, 'r')
                        else:
                            f = codecs.open(wifi_log_file, 'r', 'utf-8')   

                        f.seek(self.__fileSize, 0)

                        while True:
                            # line = f.next()
                            try:
                            	line = decode(f.readline().strip())
                            except:
                            	traceback.print_exc()
                            	break

                            if len(line) > 0:
                                with self.__cond:
                                    print(line)
                                    self.__lines.append(line + "\n")
                                    self.__cond.notify()
                            else:
                                break

                        # 更新log文件大小记录
                        self.__fileSize = getsize(wifi_log_file)
                        # self.__mtime = statinfo.st_mtime
                        print('finish reading log file, file size = %s' % self.__fileSize )
                        f.close()
                    else:
                        print('sleep 1 second')
                        time.sleep(1)
                        continue


            except:
                traceback.print_exc()

        def __update_name():
            self.__name += " [Closed]"
            self.__view.set_name(self.__name)
        sublime.set_timeout(__update_name, 0)

        # shutdown the process thread
        with self.__cond:
            self.__closing = True
            self.__cond.notify()

    def __process_thread(self):
        while True:
            with self.__cond:
                if self.__closing:
                    break
                self.__cond.wait()

            # collect more logs, for better performance
            time.sleep(0.01)
            print('process_thread wakeup')

            sublime.set_timeout(self.__check_autoscroll, 0)

            lines = None
            with self.__cond:
                lines = self.__lines
                self.__lines = []

            if len(lines) > 0:
                def gen_func(view, lines):
                    def __run():
                        view.run_command("wdb_add_line", {"data": lines})
                    return __run
                sublime.set_timeout(gen_func(self.__view, lines), 0)

    def __check_autoscroll(self):
        if self.__do_scroll:
            row, _ = self.__view.rowcol(self.__view.size())
            snap_point = self.__view.text_point(max(0, row - self.__snapLines), 0)
            snap_point = self.__view.text_to_layout(snap_point)[1]
            p = self.__view.viewport_position()[1] + self.__view.viewport_extent()[1]
            ns = p < snap_point
            if ns != self.__manual_scroll:
                self.__manual_scroll = ns
                sublime.status_message("WDB: manual scrolling enabled" if self.__manual_scroll else "ADB: automatic scrolling enabled")

    def process_lines(self, e, lines):
        overflowed = 0
        row, _ = self.__view.rowcol(self.__view.size())
        for line in lines:
            row += 1
            if row > self.__maxlines:
                overflowed += 1
            self.__view.set_read_only(False)
            self.__view.insert(e, self.__view.size(), line)
            self.__view.set_read_only(True)

            if self.__filter.search(line) == None:
                region = self.__view.line(self.__view.size()-1)
                if self.__last_fold != None:
                    self.__last_fold = self.__last_fold.cover(region)
                else:
                    self.__last_fold = region
            else:
                if self.__last_fold is not None:
                    foldregion = sublime.Region(self.__last_fold.begin()-1, self.__last_fold.end())
                    self.__view.fold(foldregion)
                self.__last_fold = None
        if overflowed > 0:
            remove_region = sublime.Region(0, self.__view.text_point(overflowed, 0))
            self.__view.set_read_only(False)
            self.__view.erase(e, remove_region)
            self.__view.set_read_only(True)
            if self.__last_fold is not None:
                self.__last_fold = sublime.Region(self.__last_fold.begin() - remove_region.size(),
                                                  self.__last_fold.end() - remove_region.size())
        if self.__last_fold is not None:
            foldregion = sublime.Region(self.__last_fold.begin()-1, self.__last_fold.end())
            self.__view.fold(foldregion)
        if self.__do_scroll and not self.__manual_scroll:
            # keep the position of horizontal scroll bar
            curr = self.__view.viewport_position()
            bottom = self.__view.text_to_layout(self.__view.size())
            self.__view.set_viewport_position((curr[0], bottom[1]), True)


class WdbAddLine(sublime_plugin.TextCommand):
    def run(self, e, data):
        length = len(wdb_views)
        if length>0:
            wdb_views[length-1].process_lines(e, data)
        


class WdbLaunch(sublime_plugin.WindowCommand):
    def run(self): 
        # sublime.message_dialog('Hello World')
        view = WDBView('wifi log')
        wdb_views.append(view)

