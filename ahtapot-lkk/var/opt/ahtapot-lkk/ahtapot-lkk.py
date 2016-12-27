#!/usr/bin/env python
#-*- coding: utf-8 -*-


from os import system
from os import kill
from os import getppid
import curses
import subprocess
from time import sleep
import logging
import sys
import os
import signal
import re


class Filelogger():


    def __init__(self,name,formatter,file_path,file_mode):
        self.name = name
        self.formatter = formatter
        self.file_path = file_path
        self.file_mode = file_mode

    def send_log(self,log_level,message):
        logging.basicConfig(format=self.formatter,filename=self.file_path,filemode=self.file_mode,level=logging.DEBUG)
        if log_level == "debug":
            logging.debug(message)
        elif log_level == "info":
            logging.info(message)
        elif log_level == "critical":
            logging.critical(message)
        elif log_level == "warning":
            logging.warning(message)
        elif log_level == "error":
            logging.error(message)
        else:
            pass

logger = Filelogger("pyOCSng",'%(asctime)s %(name)s %(levelname)s %(message)s',"/var/log/ahtapot/ahtapot-lkk.log","a")

window = curses.initscr()
curses.start_color()
curses.init_pair(1,curses.COLOR_BLACK,curses.COLOR_WHITE)
str_chose = curses.color_pair(1)
str_default = curses.A_NORMAL


screen = curses.newwin(200,200,0,0)
screen.keypad(1)
subscreen = screen.derwin(8,38,14,24)
subscreen.keypad(1)
statusscreen = screen.derwin(3,50,22,19)
statusscreen.keypad(1)

curses.raw()
curses.cbreak()


abs_path = os.path.abspath(__file__)
path_list = abs_path.split("/")
del path_list[-1]
path_name = "/".join(path_list)
full_path = path_name + "/"

log_path = "/var/log/ahtapot/fw/iptables.log"
archived_log_path = "/var/log/ahtapot/fw/iptables*log*"

def handler(signum, frame):
    raise Exception

signal.signal(signal.SIGTSTP, handler)

def check_input(inp):

    if inp == "":
        return (True, inp)
    elif inp.find("\\") == -1 and inp.find("\"") == -1 and inp.find("&") == -1 and inp.find("`") == -1 and inp.find(";") == -1 and inp.find(">") == -1 and inp.find("<") == -1:
        index = inp.find("$")
        if index != -1 and len(inp) > index+1:
            if inp[index+1] == "(":
                print " Hatali Girdi : Lutfen gecersiz karakterleri kullanmayiniz.\n"
                logger.send_log("error", "Invalid Input : " + str(inp))
                return (False, inp)
        return (True, inp)
    else:
        print " Hatali Girdi : Lutfen gecersiz karakterleri kullanmayiniz.\n"
        logger.send_log("error", "Invalid Input : " + str(inp))
        return (False, inp)


def get_param(prompt_string):
    screen.clear()
    screen.border(0)
    screen.addstr(2, 2, prompt_string)
    screen.refresh()
    input = screen.getstr(10, 10, 60)
    return input

def execute_cmd(cmd_string):
    
    system("clear")
    a = system(cmd_string)
    if a == 0:
        print "Islem Basariyla Gerceklestirildi."
    else:
        print "Islem Hata ile Sonuclandi"
    print "Ana ekran icin Enter'a basiniz..."
    try:
        raw_input("")
    except KeyboardInterrupt:
        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
        menu()
    except EOFError:
        logger.send_log("error", "EOFError While Reloading Main Screen")
        menu()
    except Exception as e:
        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
        menu()
    finally:
        menu()

def pre_grep(grep,value):

    pre_gr = ""

    if grep == "status":
        pre_gr = "|grep " + value
    elif grep == "in_eth":
        pre_gr = "|grep " + "IN=" + value
    elif grep == "out_eth":
        pre_gr = "|grep " + "OUT=" + value
    elif grep == "source":
        pre_gr = "|grep " + "SRC=" + value
    elif grep == "destination":
        pre_gr = "|grep " + "DST=" + value
    elif grep == "protocol":
        pre_gr = "|grep " + "PROTO=" + value
    elif grep == "src_port":
        pre_gr = "|grep " + "SPT=" + value
    elif grep == "dst_port":
        pre_gr = "|grep " + "DPT=" + value
    else:
        pass
    return pre_gr

def create_greps(grep_array):

    grep_cmd = ""
    for key,value in grep_array.iteritems():
        if value != "":
            grep_cmd = grep_cmd + pre_grep(key, value)

    return grep_cmd

def filter_cmd_all(grep_array,filter_cmd):
    grep_cmd = ""
    for grep in grep_array:
        grep_cmd = grep_cmd + "|" +filter_cmd + " \"" + grep + "\""
    return grep_cmd

def ask_filter_cmd(filter_cmd):
    print "*****Teker Teker Komutlarinizi Giriniz*****"
    print "-----Komut Girisini Sonlandirmak Icin Bos Birakip 'Enter' Tusuna Basiniz-----"
    x = "A"
    y = ord("A")
    grep_array = []
    while y != 34:
        status = False
        while status is not True:
            status, grep_cmd = check_input(raw_input(filter_cmd + " "))
            try:
                y = ord(grep_cmd)
                if y == 34:
                    break
            except TypeError:
                y = ord("A")
                if grep_cmd == "":
                    y = 34
                    break
            if status == True:
                grep_array.append(grep_cmd)
    return grep_array

def ask_requirements():
    
    print "*******Bilgi girmek istemediginiz alani bos birakiniz*******\n**Buyuk, Kucuk Harf Duyarliligi Vardir.**"
    x = False
    while x is not True:
        x, status = check_input(raw_input("-> Lutfen Durum Bilgisini Giriniz(ACCEPT, DROP gibi) : "))
    x = False
    while x is not True:
        x, in_eth = check_input(raw_input("-> Lutfen Giris Arabirimini Giriniz(eth0 gibi) : "))
    x = False
    while x is not True:
        x, out_eth = check_input(raw_input("-> Lutfen Cikis Arabirimini Giriniz(eth1 gibi) : "))
    x = False
    while x is not True:
        x, source = check_input(raw_input("-> Lutfen Kaynak Bilgisini Giriniz(192.168.2.21 gibi) : "))
    x = False
    while x is not True:
        x, destination = check_input(raw_input("-> Lutfen Hedef Bilgisini Giriniz(192.168.2.55 gibi) : "))
    x = False
    while x is not True:
        x, protocol = check_input(raw_input("-> Lutfen Protokol Bilgisini Giriniz(TCP, UDP gibi) : "))
    x = False
    while x is not True:
        x, src_port = check_input(raw_input("-> Lutfen Kaynak Port Bilgisini Giriniz(1514 gibi) : "))
    x = False
    while x is not True:
        x, dst_port = check_input(raw_input("-> Lutfen Hedef Port Bilgisini Giriniz(443 gibi) : "))
    return {"status":status, "in_eth" : in_eth, "out_eth" : out_eth, "source":source, "destination":destination, "protocol":protocol, "dst_port":dst_port,\
             "src_port":src_port}

def check_cmd_error(command):
    try:
        p = subprocess.Popen([command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if err:
            if re.search("No such file or directory", err):
                return (True, "HATA: Dosya veya Klasor Bulunamadı.\nLutfen /var/log/ahtapot/fw/ dizinini kontrol ediniz.")
            elif re.search("is not allowed to execute", err):
                return (True, "HATA: Komut calistirma yetkisi verilmemis.\nLutfen yoneticinize Bildiriniz.")
        return (False,False)
    except KeyboardInterrupt:
        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
        menu()
    except EOFError:
        logger.send_log("error", "EOFError While Reloading Main Screen")
        menu()
    except Exception as e:
        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
        exit()

def log_screen(mainscreen, subscreen, statusscreen):

    try:
        x = -1
        pos = 1
        while x!= 5:
            subscreen.clear()
            subscreen.border(0)
            if pos == 1:
                subscreen.addstr(1,1, "1 - Anlik Loglari Goruntule",str_chose)
            else:
                subscreen.addstr(1,1, "1 - Anlik Loglari Goruntule",str_default)
            if pos == 2:
                subscreen.addstr(2,1, "2 - Alana Gore Arama",str_chose)
            else:
                subscreen.addstr(2,1, "2 - Alana Gore Arama",str_default)
            if pos == 3:
                subscreen.addstr(3,1, "3 - Gelismis Arama",str_chose)
            else:
                subscreen.addstr(3,1, "3 - Gelismis Arama",str_default)
            if pos == 4:
                subscreen.addstr(4,1, "4 - Arsiv Loglarinda Arama",str_chose)
            else:
                subscreen.addstr(4,1, "4 - Arsiv Loglarinda Arama",str_default)
            if pos == 5:
                subscreen.addstr(5,1, "5 - Ana Menu",str_chose)
            else:
                subscreen.addstr(5,1, "5 - Ana Menu",str_default)
            mainscreen.refresh()
            subscreen.refresh()
            statusscreen.clear()
            statusscreen.border(0)
            if pos == 1:
                statusscreen.addstr(1,1, " Loglari Canli Olarak Takip Eder.",str_default)
            elif pos == 2:
                statusscreen.addstr(1,1, " Loglari Filtrelemenizi Saglar(protokol, kaynak)",str_default)
            elif pos == 3:
                statusscreen.addstr(1,1, " Loglari Belirlediginiz Komuta Gore Filtreler.",str_default)
            elif pos == 4:
                statusscreen.addstr(1,1, " Arsivlenmis loglarda Filtreleme Yapar.",str_default)
            elif pos == 5:
                statusscreen.addstr(1,1, " Ana menuye doner.",str_default)
            statusscreen.refresh()
            try:
                x = subscreen.getch()
            except KeyboardInterrupt:
                logger.send_log('error', 'Keyboard Interrupt While wating for Choice')
                menu()
            except EOFError:
                logger.send_log("error", "EOFError While Reloading Main Screen")
                menu()
            except Exception as e:
                logger.send_log('error', 'An error Occured while waiting for Choice : {} ::: line : {}'.format(str(e),str(sys.exc_info()[2].tb_lineno)))
                menu()
            if x == ord('1'):
                pos = 1
            elif x == ord('2'):
                pos = 2
            elif x == ord('3'):
                pos = 3
            elif x == ord('4'):
                pos = 4
            elif x == ord('5'):
                pos = 5
            elif x == 258:
                if pos < 5:
                    pos += 1
                else:
                    pos = 1
            elif x == 259:
                if pos > 1:
                    pos += -1
                else:
                    pos = 5
            if x == ord('\n'):
                if pos == 1:
                    curses.endwin()
                    system("clear")
                    logger.send_log("info","Tail secenegi secildi.")
                    result = check_cmd_error("ls -l " + log_path)
                    if result[0]:
                        print result[1]
                        print "***Ana Menuye Donmek Icin Enter'a Basiniz.***"
                        try:
                            raw_input("")
                        except KeyboardInterrupt:
                            logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                            menu()
                        except EOFError:
                            logger.send_log("error", "EOFError While Reloading Main Screen")
                            menu()
                        except Exception as e:
                            logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                        finally:
                            menu()
                    filter_cmd = "egrep -i"
                    system("clear")
                    screen.clear()
                    status = False
                    print ">>>Loglari Anlik Goruntuleme Menusundesiniz<<<"
                    print "Lutfen grep komutunun devamini getiriniz.\n**Buyuk, Kucuk Harf Duyarliligi Yoktur.**"
                    try:
                        while status is not True:
                            status, grep_cmd = check_input(raw_input(filter_cmd + " "))
                    except Exception as e:
                        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Waiting for Grep Command")
                        menu()
                    except KeyboardInterrupt:
                        logger.send_log("error","Keyboard Interrupt on Grep Command ")
                        menu()
                    logger.send_log("info"," EGREP cmd : " + unicode(grep_cmd))
                    try:
                        execute_cmd("sudo tail -f " + log_path + "|egrep -i \"" +  unicode(grep_cmd) + "\"")
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 2:
                    curses.endwin()
                    system("clear")
                    screen.clear()
                    print ">>>Loglari Alana Gore Filtreleme Menusundesiniz<<<"
                    logger.send_log("info","Cat secenegi secildi.\n")
                    try:
                        requirements = ask_requirements()
                    except Exception as e:
                        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except KeyboardInterrupt:
                        logger.send_log("error","Keyboard Interrupt while Getting Requirements ")
                        menu()
                    result = check_cmd_error("ls -l " + log_path)
                    if result[0]:
                        print result[1]
                        print "***Ana Menuye Donmek Icin Enter'a Basiniz.***"
                        try:
                            raw_input("")
                        except KeyboardInterrupt:
                            logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                            menu()
                        except EOFError:
                            logger.send_log("error", "EOFError While Reloading Main Screen")
                            menu()
                        except Exception as e:
                            logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                        finally:
                            menu()
                    execute_cmd("sudo cat " + log_path + create_greps(requirements) + "|less")
                elif pos == 3:
                    curses.endwin()
                    filter_cmd = "egrep -i"
                    system("clear")
                    screen.clear()
                    print ">>>Loglari Kendi Grep Komutunuzla Filtreleme Menusundesiniz<<<"
                    logger.send_log("info","Grep secenegi secildi.")
                    print "Lutfen grep komutunun devamini getiriniz.\n**Buyuk, Kucuk Harf Duyarliligi Yoktur.**"
                    try:
                        run_cmd = filter_cmd_all(ask_filter_cmd(filter_cmd), filter_cmd)
                    except Exception as e:
                        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Waiting for Grep Command")
                        menu()
                    except KeyboardInterrupt:
                        logger.send_log("error","Keyboard Interrupt on Grep Command ")
                        menu()
                    logger.send_log("info"," EGREP cmd : " + unicode(run_cmd))
                    result = check_cmd_error("ls -l " + log_path)
                    if result[0]:
                        print result[1]
                        print "***Ana Menuye Donmek Icin Enter'a Basiniz.***"
                        try:
                            raw_input("")
                            menu()
                        except KeyboardInterrupt:
                            logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                            menu()
                        except EOFError:
                            logger.send_log("error", "EOFError While Reloading Main Screen")
                            menu()
                        except Exception as e:
                            logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                            menu()
                    execute_cmd("sudo cat " + log_path + unicode(run_cmd) + "|less")
                elif pos == 4:
                    curses.endwin()
                    filter_cmd = "egrep -i"
                    system("clear")
                    screen.clear()
                    logger.send_log("info","Zcat secenegi secildi.")
                    print ">>>Gunluk Logla Birlikte Arsiv Loglari Filtreleme Menusundesiniz<<<"
                    print "Lutfen grep komutunun devamini getiriniz.\n**Buyuk, Kucuk Harf Duyarliligi Yoktur.**"
                    try:
                        run_cmd = filter_cmd_all(ask_filter_cmd(filter_cmd), filter_cmd)
                    except Exception as e:
                        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Waiting for Zcat Command")
                        menu()
                    except KeyboardInterrupt:
                        logger.send_log("error","Keyboard Interrupt on Zcat Command ")
                        menu()
                    logger.send_log("info"," ZCAT cmd : " + unicode(run_cmd))
                    result = check_cmd_error("ls -l " + archived_log_path)
                    if result[0]:
                        print result[1]
                        print "***Ana Menuye Donmek Icin Enter'a Basiniz.***"
                        try:
                            raw_input("")
                        except KeyboardInterrupt:
                            logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                            menu()
                        except EOFError:
                            logger.send_log("error", "EOFError While Reloading Main Screen")
                            menu()
                        except Exception as e:
                            logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                        finally:
                            menu()
                    execute_cmd("sudo zcat -f " + archived_log_path + unicode(run_cmd) + "|less")
                elif pos == 5:
                    logger.send_log("info"," Ana Menuye Gecis Yapildi.")
                    menu()
    except Exception as e:
        menu()

def system_screen(mainscreen, subscreen, statusscreen):

    try:
        x = -1
        pos = 1
        while x!= 6:
            subscreen.clear()
            subscreen.border(0)
            if pos == 1:
                subscreen.addstr(1,1, "1 - Disk Alani Bilgileri",str_chose)
            else:
                subscreen.addstr(1,1, "1 - Disk Alani Bilgileri",str_default)
            if pos == 2:
                subscreen.addstr(2,1, "2 - Program/IO/Hafiza/CPU Bilgileri",str_chose)
            else:
                subscreen.addstr(2,1, "2 - Program/IO/Hafiza/CPU Bilgileri",str_default)
            if pos == 3:
                subscreen.addstr(3,1, "3 - Yonlendirme Bilgileri",str_chose)
            else:
                subscreen.addstr(3,1, "3 - Yonlendirme Bilgileri",str_default)
            if pos == 4:
                subscreen.addstr(4,1, "4 - IPtables Durum Bilgileri",str_chose)
            else:
                subscreen.addstr(4,1, "4 - IPtables Durum Bilgileri",str_default)
            if pos == 5:
                subscreen.addstr(5,1, "5 - Arp Tablosu",str_chose)
            else:
                subscreen.addstr(5,1, "5 - Arp Tablosu",str_default)
            if pos == 6:
                subscreen.addstr(6,1, "6 - Ana Menu",str_chose)
            else:
                subscreen.addstr(6,1, "6 - Ana Menu",str_default)
            mainscreen.refresh()
            subscreen.refresh()
            statusscreen.clear()
            statusscreen.border(0)
            if pos == 1:
                statusscreen.addstr(1,1, " Disk Bilgilerini Yenileyerek Gosterir.",str_default)
            elif pos == 2:
                statusscreen.addstr(1,1, " Program/IO/Hafiza/CPU/Disk Bilgileri.",str_default)
            elif pos == 3:
                statusscreen.addstr(1,1, " Verilen IP icin Yonlendirme Bilgileri Gosterir.",str_default)
            elif pos == 4:
                statusscreen.addstr(1,1, " IPtables Durum Bilgisini Gosterir.",str_default)
            elif pos == 5:
                statusscreen.addstr(1,1, " Arp Tablosunu Gosterir.",str_default)
            elif pos == 6:
                statusscreen.addstr(1,1, " Ana menuye doner.",str_default)
            statusscreen.refresh()
            try:
                x = subscreen.getch()
            except KeyboardInterrupt:
                logger.send_log('error', 'Keyboard Interrupt While wating for Choice')
                menu()
            except EOFError:
                logger.send_log("error", "EOFError While Reloading Main Screen")
                menu()
            except Exception as e:
                logger.send_log('error', 'An error Occured while waiting for Choice : {} ::: line : {}'.format(str(e),str(sys.exc_info()[2].tb_lineno)))
                menu()
            if x == ord('1'):
                pos = 1
            elif x == ord('2'):
                pos = 2
            elif x == ord('3'):
                pos = 3
            elif x == ord('4'):
                pos = 4
            elif x == ord('5'):
                pos = 5
            elif x == ord('6'):
                pos = 6
            elif x == 258:
                if pos < 6:
                    pos += 1
                else:
                    pos = 1
            elif x == 259:
                if pos > 1:
                    pos += -1
                else:
                    pos = 6
            if x == ord('\n'):
                if pos == 1:
                    curses.endwin()
                    system("clear")
                    logger.send_log("info","df -h secenegi secildi.")
                    try:
                        execute_cmd("watch df -h")
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 2:
                    curses.endwin()
                    system("clear")
                    screen.clear()
                    logger.send_log("info","vmstat secenegi secildi.")
                    try:
                        execute_cmd("watch vmstat -w")
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 3:
                    curses.endwin()
                    system("clear")
                    screen.clear()
                    logger.send_log("info","mtr secenegi secildi.")
                    print ">>>Yonlendirme Bilgileri Menusundesiniz<<<"
                    print "Lutfen ip adresini giriniz."
                    try:
                        while x is not True:
                            x, ip_addr = check_input(raw_input(""))
                    except Exception as e:
                        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Waiting for Grep Command")
                        menu()
                    except KeyboardInterrupt:
                        logger.send_log("error","Keyboard Interrupt on Grep Command ")
                        menu()
                    try:
                        execute_cmd("mtr " + str(ip_addr))
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 4:
                    curses.endwin()
                    system("clear")
                    screen.clear()
                    logger.send_log("info","iptstate secenegi secildi.")
                    try:
                        execute_cmd("sudo iptstate")
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 5:
                    curses.endwin()
                    system("clear")
                    screen.clear()
                    logger.send_log("info","arp -an secenegi secildi.")
                    try:
                        execute_cmd("sudo arp -an|less")
                    except KeyboardInterrupt:
                        logger.send_log("error", "Keyboard Interrupt While Reloading Main Screen")
                        menu()
                    except EOFError:
                        logger.send_log("error", "EOFError While Reloading Main Screen")
                        menu()
                    except Exception as e:
                        logger.send_log("error", "An Error Occured While Reloading Main Screen : {} ::: line : {}".format(str(e), sys.exc_info()[2].tb_lineno))
                    finally:
                        menu()
                elif pos == 6:
                    logger.send_log("info"," Ana Menuye Gecis Yapildi.")
                    menu()
    except Exception as e:
        menu()

def menu():
    try:
        x = -1
        pos = 1
        while x!=5:
            screen.clear()
            screen.border(0)
            subscreen.border(0)
            statusscreen.border(0)
            screen.addstr(1,1,"# ________  ___  ___  _________  ________  ________  ________  _________\n\
 # |\   __  \|\  \\\  \|\___   ___\\\\   __  \|\   __  \|\   __  \|\___   ___\\\n\
 # \ \  \|\  \ \  \\\  \|___ \  \_| \  \|\  \ \  \|\  \ \  \|\  \|___ \  \_|\n\
 #  \ \   __  \ \   __ \   \ \  \ \ \   __  \ \   ____\ \  \\\  \   \ \  \\\n\
 #   \ \  \ \  \ \  \ \ \   \ \  \ \ \  \ \  \ \  \___|\ \  \\\  \   \ \  \\\n\
 #    \ \__\ \__\ \__\ \_\   \ \__\ \ \__\ \__\ \__\    \ \_______\  \ \__\\\n\
 #     \|__|\|__|\|__|\|__|   \|__|  \|__|\|__|\|__|     \|_______|   \|__|\n\
 #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=\n\
 # Limitli Kullanici Konsolu: Tum erisim ve hareketleriniz loglaniyor\n\
 #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=\n",curses.A_BOLD)
            screen.addstr(12, 20, "Lutfen Seciminizi Yapiniz ve Enter'a Basiniz.",curses.A_BOLD)
            screen.addstr(13, 13, "Islemlerden Cikmak Icin 'CTRL+C veya Q' ya basabilirsiniz.",curses.A_BOLD)

            if pos == 1:
                subscreen.addstr(1,1, "1 - IP, LAN Izleme",str_chose)
            else:
                subscreen.addstr(1,1, "1 - IP, LAN Izleme",str_default)
            if pos == 2:
                subscreen.addstr(2,1, "2 - Guvenlik Duvari Log Takibi",str_chose)
            else:
                subscreen.addstr(2,1, "2 - Guvenlik Duvari Log Takibi",str_default)
            if pos == 3:
                subscreen.addstr(3,1, "3 - Sistem Bilgileri",str_chose)
            else:
                subscreen.addstr(3,1, "3 - Sistem Bilgileri",str_default)
            if pos == 4:
                subscreen.addstr(4,1, "4 - Bant Genisligi Izleme",str_chose)
            else:
                subscreen.addstr(4,1, "4 - Bant Genisligi Izleme",str_default)
            if pos == 5:
                subscreen.addstr(5,1, "5 - Cikis",str_chose)
            else:
                subscreen.addstr(5,1, "5 - Cikis",str_default)
            screen.refresh()
            subscreen.refresh()
            if pos == 1:
                statusscreen.addstr(1,1, " IP LAN istatistiklerini Gosterir.",str_default)
            elif pos == 2:
                statusscreen.addstr(1,1, " Loglarin Takibini ve Filtrelenmesini Saglar.",str_default)
            elif pos == 3:
                statusscreen.addstr(1,1, " Sistem Bilgilerini Gormenizi Saglar.",str_default)
            elif pos == 4:
                statusscreen.addstr(1,1, " Bant Genisligi ile ilgili istatistikler.",str_default)
            elif pos == 5:
                statusscreen.addstr(1,1, " Uygulama ve Oturum Kapatilir.",str_default)
            statusscreen.refresh()
            try:
                x = subscreen.getch()
            except KeyboardInterrupt:
                logger.send_log('error', 'Keyboard Interrupt While wating for Choice')
                menu()
            except EOFError:
                logger.send_log("error", "EOFError While Reloading Main Screen")
                menu()
            except Exception as e:
                logger.send_log('error', 'An error Occured while waiting for Choice : {} ::: line : {}'.format(str(e),str(sys.exc_info()[2].tb_lineno)))
                menu()
            if x == ord('1'):
                pos = 1
            elif x == ord('2'):
                pos = 2
            elif x == ord('3'):
                pos = 3
            elif x == ord('4'):
                pos = 4
            elif x == ord('5'):
                pos = 5
            elif x == 258:
                if pos < 5:
                    pos += 1
                else:
                    pos = 1
            elif x == 259:
                if pos > 1:
                    pos += -1
                else:
                    pos = 5
            if x == ord('\n'):
                if pos == 1:
                    curses.endwin()
                    logger.send_log("info","IpTraf secenegi Secildi.")
                    execute_cmd("sudo iptraf")
                elif pos == 2:
                    curses.endwin()
                    logger.send_log("info"," Log Filtreleme Secildi.")
                    log_screen(screen, subscreen, statusscreen)
                elif pos == 3:
                    curses.endwin()
                    logger.send_log("info"," Sistem Bilgisi Secildi.")
                    system_screen(screen, subscreen, statusscreen)
                elif pos == 4:
                    curses.endwin()
                    logger.send_log("info"," Bmon Calistirildi.")
                    execute_cmd("bmon")
                elif pos == 5:
                    logger.send_log("info"," Cikis Yapildi.")
                    kill(getppid(),9)
        curses.endwin()
    except Exception as e:
        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
        menu()

if __name__ == "__main__":
    try:
        menu()
    except Exception as e:
        logger.send_log("error","An Error Occured ::: {} ::: line : ".format(str(e),str(sys.exc_info()[2].tb_lineno)))
        menu()
