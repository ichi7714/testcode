import subprocess, os
import sys
import unittest
import pyautogui as ag
from UI.gui.ui_comm_defs import UiCommDefs as ucds
from sharedmemory import SharedMemoryManager
import time
from multiprocessing import Process
from datetime import datetime
from utils.utils import getPreferenceDir, getVideoDir
from utils.common_inference_param import label_to_color, organ_param
from utils.logger import Logger
import logging

class TestUI(unittest.TestCase):
    def setUpClass():
        boot_timestamp = datetime.now()
        # TestUI.logger = Logger('ui_auto_test', boot_timestamp, logging.DEBUG)
        TestUI.logger = Logger('ui_auto_test', boot_timestamp)

        TestUI.logger.info("setUpClass started.")
        if os.path.isfile("ui_debug"):
            command = "mv ui_debug ui_debug.save"
            TestUI.logger.info("setUpClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))

        command = "echo 1 > ui_debug"
        TestUI.logger.info("setUpClass:: cmd: {}".format(command))
        cp = subprocess.run(command, shell=True, encoding='utf-8')
        if cp.returncode != 0:
            TestUI.logger.error('{} failed.'.format(command))

        color_cfg = str(getPreferenceDir()/"color_cfg.txt")
        if os.path.isfile(color_cfg):
            command = "cp "+color_cfg+" "+color_cfg+".save"
            TestUI.logger.info("setUpClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))

        chapter_file = str(getVideoDir()/".胃＿ダヴィンチ＿膵上縁25シーン＿結合組織用_0_60.chapter")
        if os.path.isfile(chapter_file):
            command = "mv "+chapter_file+" "+chapter_file+".save"
            TestUI.logger.info("setUpClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))


        boot_timestamp = datetime.now()
        TestUI.smmgr = SharedMemoryManager()

        TestUI.logger.info("setUpClass:: Launch UI module.")
        TestUI.process_ui = Process(target=TestUI.run_ui, args=[boot_timestamp, TestUI.smmgr])
        TestUI.process_ui.start()
        time.sleep(3)

        TestUI.color_cfgs = []
        TestUI.read_color_cfg(TestUI.color_cfgs)

        TestUI.logger.info("setUpClass:: Auto Test start.")
        TestUI.screen_x, TestUI.screen_y = ag.size()
        TestUI.logger.info("screen size:{}x{}".format(TestUI.screen_x, TestUI.screen_y))

        x = TestUI.calc_xpos(ucds.ANAUT_BUTTON_X)
        y = TestUI.calc_ypos(ucds.ANAUT_BUTTON_Y)

        TestUI.logger.info("Anaut Button position:{}x{}".format(x, y))

        # ag.moveTo(x, y, duration=0.5)
        ag.click(x, y, button="left")
        TestUI.logger.info("setUpClass:: Pushed Anaut button({},{})".format(x, y))
        time.sleep(0.5)

    def tearDownClass():
        TestUI.logger.info("tearDownClass started.")

        command = "rm -f ui_debug"
        TestUI.logger.info("tearDownClass:: cmd: {}".format(command))
        cp = subprocess.run(command, shell=True, encoding='utf-8')
        if cp.returncode != 0:
            TestUI.logger.error('{} failed.'.format(command))

        if os.path.isfile("ui_debug.save"):
            command = "mv -f ui_debug.save ui_debug"
            TestUI.logger.info("tearDownClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))

        x = TestUI.calc_xpos(ucds.QUIT_BUTTON_X)
        y = TestUI.calc_ypos(ucds.QUIT_BUTTON_Y)
        TestUI.logger.info("Quit Button position:{}x{}".format(x, y))

        # ag.moveTo(x, y, duration=0.5)
        ag.click(x, y, button="left")
        TestUI.logger.info("tearDownClass:: Pushed Quit button({},{})".format(x, y))
        TestUI.smmgr.set_quit()
        TestUI.process_ui.join()

        color_cfg = str(getPreferenceDir()/"color_cfg.txt")
        if os.path.isfile(color_cfg+".save"):
            command = "mv -f "+color_cfg+".save"+" "+color_cfg
            TestUI.logger.info("setUpClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))

        chapter_file = str(getVideoDir()/".胃＿ダヴィンチ＿膵上縁25シーン＿結合組織用_0_60.chapter")
        if os.path.isfile(chapter_file+".save"):
            command = "mv -f "+chapter_file+".save"+" "+chapter_file
            TestUI.logger.info("setUpClass:: cmd: {}".format(command))
            cp = subprocess.run(command, shell=True, encoding='utf-8')
            if cp.returncode != 0:
                TestUI.logger.error('{} failed.'.format(command))

    def setUp(self):
        pass
        # TestUI.logger.info("setUp started.")

    def tearDown(self):
        pass
        # TestUI.logger.info("tearDown started.")

    def read_color_cfg(color_cfgs):
        COLOR_CFG_FILE = str(getPreferenceDir()/"color_cfg.txt")
        try:
            with open(COLOR_CFG_FILE, "r", encoding = "utf-8") as cc:
                lines = cc.readlines()
            cc.close()

            if len(lines) > 0:
                for i, line in enumerate(lines):
                    color_str = line.rstrip('\n')
                    if i < len(ucds.default_colors) and color_str != ucds.default_colors[i]:
                        color_str = ucds.default_colors[i]

                    colors = [int(c) for c in list(color_str.split(','))[:3]]
                    color_cfgs.append(colors)
                    TestUI.logger.debug("read_color_cfg:: color_str:{}".format(color_str))
            else:
                TestUI.logger.debug("read_color_cfg:: {} file is empty !!".format(COLOR_CFG_FILE))

        except FileNotFoundError:
            TestUI.logger.error("read_color_cfg:: {} file not found !!".format(COLOR_CFG_FILE))
        except:
            TestUI.logger.error("read_color_cfg:: Unexpected error: {}".format(sys.exc_info()[0]))

    def run_ui(boot_timestamp: datetime, smmgr: SharedMemoryManager) -> None:
        '''UIサブプロセス
        @param  boot_timestamp  最初にログ出力するタイムスタンプ
        @param  smmgr           共有メモリマネージャ
        '''
        from UI.trt_inference_ui import TrtInferenceApp
        TrtInferenceApp(boot_timestamp, smmgr).run()

    def calc_xpos(x):
        return x+10

    def calc_ypos(y):
        return TestUI.screen_y-y-10
        
    def push_button(self, x, y):
        px = TestUI.calc_xpos(x)
        py = TestUI.calc_ypos(y)
        ag.moveTo(px, py)
        ag.click(px, py, button="left")
        return px, py

    def test_output(self):
        TestUI.logger.info("test_output started.")
        SOFTMAP_Y = 716
        OVERLAY_Y = 682

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, OVERLAY_Y)
        time.sleep(0.5)
        changed, output = TestUI.smmgr.get_output_style()
        TestUI.logger.info("Pushed overlay button({},{}) Expected:{} Result:{}".format(x, y, "overlay_torch", output))
        self.assertEqual("overlay_torch", output)

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, SOFTMAP_Y)
        time.sleep(0.5)
        changed, output = TestUI.smmgr.get_output_style()
        TestUI.logger.info("Pushed softmap button({},{}) Expected:{} Result:{}".format(x, y, "softmap_torch", output))
        self.assertEqual("softmap_torch", output)

        TestUI.logger.info("test_output completed.")

    def test_average(self):
        TestUI.logger.info("test_average started.")
        AVERAGE_Y = 530

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, AVERAGE_Y)
        time.sleep(0.5)
        changed, average = TestUI.smmgr.get_do_average()
        TestUI.logger.info("Pushed Average button({},{}) Expected:{} Result:{}".format(x, y, True, average))
        self.assertTrue(average)

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, AVERAGE_Y)
        time.sleep(0.5)
        changed, average = TestUI.smmgr.get_do_average()
        TestUI.logger.info("Pushed Average button({},{}) Expected:{} Result:{}".format(x, y, False, average))
        self.assertFalse(average)

        TestUI.logger.info("test_average completed.")

    def test_inference(self):
        TestUI.logger.info("test_inference started.")
        INFERENCE_Y = 304

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, INFERENCE_Y)
        time.sleep(0.5)
        inference = TestUI.smmgr.is_do_inference()
        TestUI.logger.info("Pushed Inference button({},{}) Expected:{} Result:{}".format(x, y, False, inference))
        self.assertFalse(inference)

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, INFERENCE_Y)
        time.sleep(0.5)
        inference = TestUI.smmgr.is_do_inference()
        TestUI.logger.info("Pushed Inference button({},{}) Expected:{} Result:{}".format(x, y, True, inference))
        self.assertTrue(inference)

        TestUI.logger.info("test_inference completed.")

    def test_inference_timer(self):
        TestUI.logger.info("test_inference_timer started.")
        INFERENCE_TIMER_Y = 254

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, INFERENCE_TIMER_Y)
        time.sleep(0.5)
        inference = TestUI.smmgr.is_do_inference()
        TestUI.logger.info("Pushed Inference Timer button({},{}) Expected:{} Result:{}".format(x, y, False, inference))
        self.assertFalse(inference)

        time.sleep(5)
        inference = TestUI.smmgr.is_do_inference()
        TestUI.logger.info("Inference Timer button({},{}) Result:{}".format(x, y, True, inference))
        self.assertTrue(inference)

        TestUI.logger.info("test_inference_timer completed.")

    def test_color_register(self):
        TestUI.logger.info("test_color_register started.")
        COLOR_REGISTER_Y = 497
        COLOR_PALETTE_Y = 374
        PALETTE_SIZE = 20

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, COLOR_PALETTE_Y-PALETTE_SIZE)
        time.sleep(0.5)
        changed, label_name, selected_colors = TestUI.smmgr.get_label_color()
        x, y = self.push_button(ucds.CTRL_BUTTONS_X, COLOR_REGISTER_Y)
        time.sleep(0.5)

        for i, expected_colors in enumerate(TestUI.color_cfgs):
            xp = i%5
            yp = 0 if i < 5 else 1
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+xp*PALETTE_SIZE, COLOR_PALETTE_Y-yp*PALETTE_SIZE)
            time.sleep(0.5)

        x, y = self.push_button(ucds.CTRL_BUTTONS_X, COLOR_REGISTER_Y)
        time.sleep(0.5)

        for i, expected_colors in enumerate(TestUI.color_cfgs):
            xp = i%5
            yp = 0 if i < 5 else 1
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+xp*PALETTE_SIZE, COLOR_PALETTE_Y-yp*PALETTE_SIZE)
            time.sleep(0.5)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            if i < len(ucds.default_colors):
                TestUI.logger.info("Pushed Color Palette button({},{}) Expected:{} Result:{}".format(x, y, expected_colors, colors))
                self.assertEqual(expected_colors, colors)
            else:
                TestUI.logger.info("Pushed Color Palette button({},{}) Expected:{} Result:{}".format(x, y, selected_colors, colors))
                self.assertEqual(selected_colors, colors)

        TestUI.logger.info("test_color_register completed.")

    def color_palette_test(self, expected_label_name):
        TestUI.logger.info("color_palette_test started.")
        COLOR_PALETTE_Y = 374
        PALETTE_SIZE = 20

        for i, expected_colors in enumerate(TestUI.color_cfgs):
            xp = i%5
            yp = 0 if i < 5 else 1
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+xp*PALETTE_SIZE, COLOR_PALETTE_Y-yp*PALETTE_SIZE)
            time.sleep(0.5)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color Palette button({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_colors, label_name, colors))
            self.assertEqual(expected_label_name, label_name)
            self.assertEqual(expected_colors, colors)

        TestUI.logger.info("color_palette_test completed.")

    def test_color_palette(self):
        TestUI.logger.info("test_color_palette started.")
        CON_PANEL_MENU_Y = 875
        NERV_PANEL_MENU_Y = 845
        PAN_PANEL_MENU_Y = 816
        URE_PANEL_MENU_Y = 784
        COLOR_PALETTE_Y = 374
        PALETTE_SIZE = 20
        models = {"connective tissue":CON_PANEL_MENU_Y,\
                  "nerve":NERV_PANEL_MENU_Y,\
                  "pancreatic parenchyma":PAN_PANEL_MENU_Y,\
                  "ureter":URE_PANEL_MENU_Y}
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+PALETTE_SIZE, COLOR_PALETTE_Y-PALETTE_SIZE)
        changed, label_name, colors = TestUI.smmgr.get_label_color()
        time.sleep(0.5)

        for el, yp in models.items():
            if el != "connective tissue":
                x, y = self.push_button(ucds.CTRL_BUTTONS_X, yp)
                time.sleep(0.5)
                changed, model_name = TestUI.smmgr.get_model_name()
                TestUI.logger.info("Pushed Model Panel Menu button({},{}) Result:{}".format(x, y, model_name))

            self.color_palette_test(el)

        TestUI.logger.info("test_color_palette completed.")

    def test_color_bar(self):
        TestUI.logger.info("test_color_bar started.")
        R_COLOR_BAR_Y = 478
        G_COLOR_BAR_Y = 453
        B_COLOR_BAR_Y = 428
        color_bars = [R_COLOR_BAR_Y, G_COLOR_BAR_Y, B_COLOR_BAR_Y]
        expected_color = {0:0, 43:129, 53:192, 80:255}

        expected_label_name = "connective tissue"
        for i, yp in enumerate(color_bars):
            x_offset = 43
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+x_offset, yp)
            time.sleep(1)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color bar({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_color[x_offset], label_name, colors[i]))
            self.assertEqual(expected_label_name, label_name)
            self.assertEqual(expected_color[x_offset], colors[i])

            x_offset = 0
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+x_offset, yp)
            time.sleep(0.5)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color bar({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_color[x_offset], label_name, colors[i]))
            self.assertEqual(expected_color[x_offset], colors[i])

            x_offset = 43
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+x_offset, yp)
            time.sleep(1)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color bar({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_color[x_offset], label_name, colors[i]))
            self.assertEqual(expected_color[x_offset], colors[i])

            x_offset = 53
            ag.dragRel(18, 0, duration=0.5)
            time.sleep(1)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color bar({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_color[x_offset], label_name, colors[i]))
            self.assertEqual(expected_color[x_offset], colors[i])

            x_offset = 80
            x, y = self.push_button(ucds.CTRL_BUTTONS_X+x_offset, yp)
            time.sleep(0.5)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pushed Color bar({},{}) Expected:{}/{} Result:{}/{}".format(x, y, expected_label_name, expected_color[x_offset], label_name, colors[i]))
            self.assertEqual(expected_color[x_offset], colors[i])

        TestUI.logger.info("test_color_bar completed.")

    def test_model_panel_menu(self):
        TestUI.logger.info("test_model_panel_menu started.")
        CON_PANEL_MENU_Y = 875
        NERV_PANEL_MENU_Y = 845
        PAN_PANEL_MENU_Y = 816
        URE_PANEL_MENU_Y = 784
        models = {"connective tissue":{"ypos":CON_PANEL_MENU_Y,"def_model":"con_deeplab_origi_trt_model"},\
                  "nerve":{"ypos":NERV_PANEL_MENU_Y,"def_model":"ner_deeplab_origi_conig_control_base16_trt_model"},\
                  "pancreatic parenchyma":{"ypos":PAN_PANEL_MENU_Y,"def_model":"pan_June_DLOv2"},\
                  "ureter":{"ypos":URE_PANEL_MENU_Y,"def_model":"ure_DLOv2"}}

        for on, info in models.items():
            model_def_param = organ_param[on]
            x, y = self.push_button(ucds.CTRL_BUTTONS_X, info["ypos"])
            time.sleep(0.5)
            changed, model_name = TestUI.smmgr.get_model_name()
            TestUI.logger.info("Pushed Model Panel Menu button({},{}) Expected:{} Result:{}".format(x, y, info["def_model"], model_name))
            self.assertEqual(info["def_model"], model_name)

            expected_output = model_def_param["style"]
            changed, output = TestUI.smmgr.get_output_style()
            TestUI.logger.info("Default Output Style:: Expected:{} Result:{}".format(expected_output, output))
            self.assertEqual(expected_output, output)

            expected_thresh = float(model_def_param['thresh'])
            changed, thresh = TestUI.smmgr.get_thresh()
            TestUI.logger.info("Default Threshold:: Expected:{} Result:{}".format(expected_thresh, thresh))
            self.assertAlmostEqual(expected_thresh, thresh)

            expected_max_conf = float(model_def_param['max-conf'])
            changed, max_conf = TestUI.smmgr.get_max_conf()
            TestUI.logger.info("Default Max Conf.:: Expected:{} Result:{}".format(expected_max_conf, max_conf))
            self.assertAlmostEqual(expected_max_conf, max_conf)

            expected_average = model_def_param['do_average_canvas']
            changed, average = TestUI.smmgr.get_do_average()
            TestUI.logger.info("Default Average.:: Expected:{} Result:{}".format(expected_average, average))
            if expected_average:
                self.assertTrue(average)
            else:
                self.assertFalse(average)

            expected_colors = list(label_to_color[on])
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Default Colors.:: Expected:{} Result:{}".format(expected_colors, colors))
            self.assertEqual(on, label_name)
            self.assertEqual(expected_colors, colors)

        TestUI.logger.info("test_model_panel_menu completed.")

    def model_menu_hover_test(self, models):
        TestUI.logger.info("model_menu_hover_test started.")
        CON_PANEL_MENU_Y = 875
        COLOR_PALETTE_Y = 374
        PALETTE_SIZE = 20
        
        x, y = self.push_button(ucds.CTRL_BUTTONS_X, CON_PANEL_MENU_Y)
        changed, selected_model_name = TestUI.smmgr.get_model_name()
        TestUI.logger.info("Selected Model  ({},{}) Result:{}".format(x, y, selected_model_name))
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+4*PALETTE_SIZE, COLOR_PALETTE_Y-PALETTE_SIZE)
        changed, label_name, selected_colors = TestUI.smmgr.get_label_color()
        TestUI.logger.info("Selected Model Color ({},{}) Result:{}".format(x, y, selected_colors))

        panel_mode = True
        if models["connective tissue"]["xpos"] != ucds.CTRL_BUTTONS_X:
            panel_mode = False
            x = TestUI.calc_xpos(models["connective tissue"]["xpos"])
            y = TestUI.calc_ypos(models["connective tissue"]["ypos"])
            ag.moveTo(x, y)
            ag.rightClick(x, y)
            TestUI.logger.info("Root Menu: ({},{})".format(x, y))

        for on, info in models.items():
            model_def_param = organ_param[on]
            model_def_color = list(label_to_color[on])
            px = TestUI.calc_xpos(info["xpos"])
            py = TestUI.calc_ypos(info["ypos"])
            if not panel_mode:
                px += 50
                py += 50
            ag.moveTo(px, py)
            changed, model_name = TestUI.smmgr.get_model_name()
            TestUI.logger.info("Pointed Model Menu: ({},{}) Expected:{} Result:{}".format(px, py, selected_model_name, model_name))
            self.assertEqual(selected_model_name, model_name)
            changed, label_name, colors = TestUI.smmgr.get_label_color()
            TestUI.logger.info("Pointed Model Menu Color: Expected:{} Result:{}".format(selected_colors, colors))
            self.assertEqual(selected_colors, colors)

            for i in range(info["sub_nemus"]):
                if panel_mode:
                    x_offset = -50
                    y_offset = i*26
                else:
                    x_offset = 80
                    y_offset = i*27+8
                ag.moveTo(px+x_offset, py+y_offset, duration=0.5)
                time.sleep(0.5)
                changed, model_name = TestUI.smmgr.get_model_name()
                TestUI.logger.info("Pointed Model: ({},{}) Expected:{} Result:{}".format(px+x_offset, py+y_offset, info["name"][i], model_name))
                self.assertEqual(info["name"][i], model_name)

                changed, label_name, colors = TestUI.smmgr.get_label_color()
                if selected_model_name == model_name:
                    TestUI.logger.info("Pointed Model Color: Expected:{} Result:{}".format(selected_colors, colors))
                    self.assertEqual(selected_colors, colors)
                else:
                    TestUI.logger.info("Pointed Model Color: Expected:{} Result:{}".format(model_def_color, colors))
                    self.assertEqual(model_def_color, colors)

        TestUI.logger.info("model_menu_hover_test completed.")

    def test_model_panel_menu_hover(self):
        TestUI.logger.info("test_model_panel_menu_hover started.")
        MENU_X = ucds.CTRL_BUTTONS_X
        CON_PANEL_MENU_Y = 875
        NERV_PANEL_MENU_Y = 840
        PAN_PANEL_MENU_Y = 816
        URE_PANEL_MENU_Y = 784
        models = {"connective tissue":{"xpos":MENU_X,"ypos":CON_PANEL_MENU_Y,"sub_nemus":4,\
                                       "name":[ "con_deeplab_origi_trt_model",\
                                                "con_unet_trt_model",\
                                                "con_laddernet_trt_model",\
                                                "con_deeplab_trt_model"]},\
                  "nerve":{"xpos":MENU_X,"ypos":NERV_PANEL_MENU_Y,"sub_nemus":5,\
                            "name":["ner_deeplab_origi_conig_control_base32_trt_model",\
                                    "ner_deeplab_origi_conig_control_base16_trt_model",\
                                    "ner_unet_trt_model",\
                                    "ner_laddernet_trt_model",\
                                    "ner_deeplab_v3plus_trt_model"]},\
                  "pancreatic parenchyma":{"xpos":MENU_X,"ypos":PAN_PANEL_MENU_Y,"sub_nemus":3,\
                                          "name":[  "pan_166_DLOv1",\
                                                    "pan_166_DLOv2",\
                                                    "pan_June_DLOv2"]},\
                  "ureter":{"xpos":MENU_X,"ypos":URE_PANEL_MENU_Y,"sub_nemus":3,\
                            "name":["ure_DLOv1",\
                                    "ure_DLOv2",\
                                    "ure_DLv3"]}}

        self.model_menu_hover_test(models)

        TestUI.logger.info("test_model_panel_menu_hover completed.")

    def test_model_root_menu_hover(self):
        TestUI.logger.info("test_model_root_menu_hover started.")
        MENU_X = 800
        OFFSET_Y = 450
        CON_PANEL_MENU_Y = 875-OFFSET_Y
        NERV_PANEL_MENU_Y = 835-OFFSET_Y
        PAN_PANEL_MENU_Y = 795-OFFSET_Y
        URE_PANEL_MENU_Y = 755-OFFSET_Y
        models = {"connective tissue":{"xpos":MENU_X,"ypos":CON_PANEL_MENU_Y,"sub_nemus":4,\
                                       "name":[ "con_deeplab_origi_trt_model",\
                                                "con_unet_trt_model",\
                                                "con_laddernet_trt_model",\
                                                "con_deeplab_trt_model"]},\
                  "nerve":{"xpos":MENU_X,"ypos":NERV_PANEL_MENU_Y,"sub_nemus":5,\
                            "name":["ner_deeplab_origi_conig_control_base32_trt_model",\
                                    "ner_deeplab_origi_conig_control_base16_trt_model",\
                                    "ner_unet_trt_model",\
                                    "ner_laddernet_trt_model",\
                                    "ner_deeplab_v3plus_trt_model"]},\
                  "pancreatic parenchyma":{"xpos":MENU_X,"ypos":PAN_PANEL_MENU_Y,"sub_nemus":3,\
                                          "name":[  "pan_166_DLOv1",\
                                                    "pan_166_DLOv2",\
                                                    "pan_June_DLOv2"]},\
                  "ureter":{"xpos":MENU_X,"ypos":URE_PANEL_MENU_Y,"sub_nemus":3,\
                            "name":["ure_DLOv1",\
                                    "ure_DLOv2",\
                                    "ure_DLv3"]}}

        self.model_menu_hover_test(models)

        TestUI.logger.info("test_model_root_menu_hover completed.")

    def model_select_test(self, models):
        TestUI.logger.info("model_select_test started.")
        CON_PANEL_MENU_Y = 875
        COLOR_PALETTE_Y = 374
        PALETTE_SIZE = 20
        
        panel_mode = True
        if models["connective tissue"]["xpos"] != ucds.CTRL_BUTTONS_X:
            panel_mode = False
            x = TestUI.calc_xpos(models["connective tissue"]["xpos"])
            y = TestUI.calc_ypos(models["connective tissue"]["ypos"])
            ag.moveTo(x, y)
            ag.rightClick(x, y)
            TestUI.logger.info("Root Menu: ({},{})".format(x, y))

        max_menus = max([info["sub_nemus"] for info in models.values()])
        for i in reversed(range(max_menus)):
            for on, info in models.items():
                TestUI.logger.info("Selected Model Menu: on:{}({})".format(on, i))
                if i < info["sub_nemus"]:
                    model_def_param = organ_param[on]
                    model_def_color = list(label_to_color[on])
                    px = TestUI.calc_xpos(info["xpos"])
                    py = TestUI.calc_ypos(info["ypos"])
                    if not panel_mode:
                        px += 50
                        py += 50
                        ag.moveTo(x, y)
                        ag.rightClick(x, y)
                    ag.moveTo(px, py)
                    TestUI.logger.info("Selected Model Menu: ({},{}) on:{}({})".format(px, py, on, i))
                    # time.sleep(1)

                    if panel_mode:
                        x_offset = -50
                        y_offset = i*26
                    else:
                        x_offset = 80
                        y_offset = i*27+8
                    ag.moveTo(px+x_offset, py)
                    ag.moveTo(px+x_offset, py+y_offset, duration=0.5)
                    ag.click(px+x_offset, py+y_offset, button="left")
                    time.sleep(0.5)
                    changed, model_name = TestUI.smmgr.get_model_name()
                    TestUI.logger.info("Selected Model: ({},{}) Expected:{} Result:{}".format(px+x_offset, py+y_offset, info["name"][i], model_name))
                    self.assertEqual(info["name"][i], model_name)

                    changed, label_name, colors = TestUI.smmgr.get_label_color()
                    TestUI.logger.info("Selected Model Color: Expected:{} Result:{}".format(model_def_color, colors))
                    self.assertEqual(model_def_color, colors)

                    command = "ls -rt log/*_ui* | tail -1"
                    cp = subprocess.run(command, shell=True, encoding='utf-8', stdout=subprocess.PIPE)
                    fn = cp.stdout.rstrip('\n')
                    command = "cat "+fn+" | grep \"Selected Model Titl\" | tail -1"
                    cp = subprocess.run(command, shell=True, encoding='utf-8', stdout=subprocess.PIPE)

                    mlabel = cp.stdout.rsplit(":")[-1].rstrip('\n')
                    TestUI.logger.info("Selected Model Label: Expected:{} Result:{}".format(info["label"][i], mlabel))
                    self.assertEqual(info["label"][i], mlabel)

        TestUI.logger.info("model_select_test completed.")

    def test_model_select_panel_menu(self):
        TestUI.logger.info("test_model_select_panel_menu started.")
        MENU_X = ucds.CTRL_BUTTONS_X
        CON_PANEL_MENU_Y = 875
        NERV_PANEL_MENU_Y = 835
        PAN_PANEL_MENU_Y = 816
        URE_PANEL_MENU_Y = 784
        models = {  "connective tissue":{   "xpos":MENU_X,"ypos":CON_PANEL_MENU_Y,"sub_nemus":4,\
                                            "name":["con_deeplab_origi_trt_model",\
                                                    "con_unet_trt_model",\
                                                    "con_laddernet_trt_model",\
                                                    "con_deeplab_trt_model"],\
                                            "label":[   "Connective/DLO",\
                                                        "Connective/Unet",\
                                                        "Connective/Laddernet",\
                                                        "Connective/Deeplab"]},\
                    "nerve":{   "xpos":MENU_X,"ypos":NERV_PANEL_MENU_Y,"sub_nemus":5,\
                                "name":[    "ner_deeplab_origi_conig_control_base32_trt_model",\
                                            "ner_deeplab_origi_conig_control_base16_trt_model",\
                                            "ner_unet_trt_model",\
                                            "ner_laddernet_trt_model",\
                                            "ner_deeplab_v3plus_trt_model"],\
                                "label":[   "Nerves/DLO V2",\
                                            "Nerves/DLO",\
                                            "Nerves/Unet",\
                                            "Nerves/Laddernet",\
                                            "Nerves/Deeplab"]},\
                    "pancreatic parenchyma":{   "xpos":MENU_X,"ypos":PAN_PANEL_MENU_Y,"sub_nemus":3,\
                                                "name":["pan_166_DLOv1",\
                                                        "pan_166_DLOv2",\
                                                        "pan_June_DLOv2"],\
                                                "label":[   "Pancreas/DLO V1",\
                                                            "Pancreas/DLO V2 166",\
                                                            "Pancreas/DLO V2"]},\
                    "ureter":{  "xpos":MENU_X,"ypos":URE_PANEL_MENU_Y,"sub_nemus":3,\
                                "name":["ure_DLOv1",\
                                        "ure_DLOv2",\
                                        "ure_DLv3"],\
                                "label":[   "Ureter/DLO V1",\
                                            "Ureter/DLO V2",\
                                            "Ureter/DL V3"]}    }

        self.model_select_test(models)

        TestUI.logger.info("test_model_select_panel_menu completed.")

    def test_model_select_root_menu(self):
        TestUI.logger.info("test_model_select_root_menu started.")
        MENU_X = 800
        OFFSET_Y = 450
        CON_PANEL_MENU_Y = 875-OFFSET_Y
        NERV_PANEL_MENU_Y = 835-OFFSET_Y
        PAN_PANEL_MENU_Y = 795-OFFSET_Y
        URE_PANEL_MENU_Y = 755-OFFSET_Y
        models = {  "connective tissue":{   "xpos":MENU_X,"ypos":CON_PANEL_MENU_Y,"sub_nemus":4,\
                                            "name":["con_deeplab_origi_trt_model",\
                                                    "con_unet_trt_model",\
                                                    "con_laddernet_trt_model",\
                                                    "con_deeplab_trt_model"],\
                                            "label":[   "Connective/DLO",\
                                                        "Connective/Unet",\
                                                        "Connective/Laddernet",\
                                                        "Connective/Deeplab"]},\
                    "nerve":{   "xpos":MENU_X,"ypos":NERV_PANEL_MENU_Y,"sub_nemus":5,\
                                "name":[    "ner_deeplab_origi_conig_control_base32_trt_model",\
                                            "ner_deeplab_origi_conig_control_base16_trt_model",\
                                            "ner_unet_trt_model",\
                                            "ner_laddernet_trt_model",\
                                            "ner_deeplab_v3plus_trt_model"],\
                                "label":[   "Nerves/DLO V2",\
                                            "Nerves/DLO",\
                                            "Nerves/Unet",\
                                            "Nerves/Laddernet",\
                                            "Nerves/Deeplab"]},\
                    "pancreatic parenchyma":{   "xpos":MENU_X,"ypos":PAN_PANEL_MENU_Y,"sub_nemus":3,\
                                                "name":["pan_166_DLOv1",\
                                                        "pan_166_DLOv2",\
                                                        "pan_June_DLOv2"],\
                                                "label":[   "Pancreas/DLO V1",\
                                                            "Pancreas/DLO V2 166",\
                                                            "Pancreas/DLO V2"]},\
                    "ureter":{  "xpos":MENU_X,"ypos":URE_PANEL_MENU_Y,"sub_nemus":3,\
                                "name":["ure_DLOv1",\
                                        "ure_DLOv2",\
                                        "ure_DLv3"],\
                                "label":[   "Ureter/DLO V1",\
                                            "Ureter/DLO V2",\
                                            "Ureter/DL V3"]}    }

        self.model_select_test(models)

        TestUI.logger.info("test_model_select_root_menu completed.")

    def test_threshold(self):
        TestUI.logger.info("test_threshold started.")
        THRESHOLD_Y = 632

        expected_thresh = 1.0
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+90, THRESHOLD_Y)
        time.sleep(2)
        changed, thresh = TestUI.smmgr.get_thresh()
        TestUI.logger.info("Pushed Threshold bar({},{}) Expected:{} Result:{}".format(x, y, expected_thresh, thresh))
        self.assertAlmostEqual(expected_thresh, thresh)

        expected_thresh = 0.5
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+50, THRESHOLD_Y)
        time.sleep(0.5)
        changed, thresh = TestUI.smmgr.get_thresh()
        TestUI.logger.info("Pushed Threshold bar({},{}) Expected:{} Result:{}".format(x, y, expected_thresh, thresh))
        self.assertAlmostEqual(expected_thresh, thresh)

        expected_thresh = 0.2
        ag.dragRel(-20, 0, duration=0.5)
        time.sleep(0.5)
        changed, thresh = TestUI.smmgr.get_thresh()
        TestUI.logger.info("Pushed Threshold bar({},{}) Expected:{} Result:{}".format(x-20, y, expected_thresh, thresh))
        self.assertAlmostEqual(expected_thresh, thresh)

        expected_thresh = 0.0
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+10, THRESHOLD_Y)
        time.sleep(0.5)
        changed, thresh = TestUI.smmgr.get_thresh()
        TestUI.logger.info("Pushed Threshold bar({},{}) Expected:{} Result:{}".format(x, y, expected_thresh, thresh))
        self.assertAlmostEqual(expected_thresh, thresh)

        TestUI.logger.info("test_threshold completed.")

    def test_max_conf(self):
        TestUI.logger.info("test_max_conf started.")
        MAX_CONF_Y = 570

        expected_max_conf = 0.0
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+10, MAX_CONF_Y)
        time.sleep(0.5)
        changed, max_conf = TestUI.smmgr.get_max_conf()
        TestUI.logger.info("Pushed Max Opacity bar({},{}) Expected:{} Result:{}".format(x, y, expected_max_conf, max_conf))
        self.assertAlmostEqual(expected_max_conf, max_conf)

        expected_max_conf = 0.5
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+50, MAX_CONF_Y)
        time.sleep(0.5)
        changed, max_conf = TestUI.smmgr.get_max_conf()
        TestUI.logger.info("Pushed Max Opacity bar({},{}) Expected:{} Result:{}".format(x, y, expected_max_conf, max_conf))
        self.assertAlmostEqual(expected_max_conf, max_conf)

        expected_max_conf = 0.8
        ag.dragRel(20, 0, duration=0.5)
        time.sleep(0.5)
        changed, max_conf = TestUI.smmgr.get_max_conf()
        TestUI.logger.info("Pushed Max Opacity bar({},{}) Expected:{} Result:{}".format(x+20, y, expected_max_conf, max_conf))
        self.assertAlmostEqual(expected_max_conf, max_conf)

        expected_max_conf = 1.0
        x, y = self.push_button(ucds.CTRL_BUTTONS_X+90, MAX_CONF_Y)
        time.sleep(0.5)
        changed, max_conf = TestUI.smmgr.get_max_conf()
        TestUI.logger.info("Pushed Max Opacity bar({},{}) Expected:{} Result:{}".format(x, y, expected_max_conf, max_conf))
        self.assertAlmostEqual(expected_max_conf, max_conf)

        TestUI.logger.info("test_max_conf completed.")

    def test_video_mode(self):
        TestUI.logger.info("test_video_mode started.")
        VIDEO_Y = 60
        VIDEO_SELECT_X = 1017
        VIDEO_SELECT_Y = 425
        VIDEO_LOAD_X = 1153
        VIDEO_LOAD_Y = 125
        VIDEO_CTRL_Y = 20
        FAST_BACK_X = 865
        FB_10SEC_X = 917
        PLAY_PAUSE_X = 969
        FF_10SEC_X = 1021
        FAST_FORWARD_X = 1066
        CHAPTER_X = 1113
        REVIEW_BAR_START_X = 15
        REVIEW_BAR_END_X = 1816
        REVIEW_BAR_Y = 40

        chapter_file = str(getVideoDir()/".胃＿ダヴィンチ＿膵上縁25シーン＿結合組織用_0_60.chapter")
        command = 'echo 0\\\\n500\\\\n1000\\\\n1500 > '+chapter_file
        TestUI.logger.info("test_video_mode:: cmd: {}".format(command))
        cp = subprocess.run(command, shell=True, encoding='utf-8')
        if cp.returncode != 0:
            TestUI.logger.error('{} failed.'.format(command))
        command = "cat "+chapter_file
        TestUI.logger.info("test_video_mode:: cmd: {}".format(command))
        cp = subprocess.run(command, shell=True, encoding='utf-8')

        x, y = self.push_button(ucds.CTRL_BUTTONS_X+10, VIDEO_Y)
        time.sleep(0.5)
        TestUI.logger.info("Pushed Video Mode({},{})".format(x, y))

        x, y = self.push_button(VIDEO_SELECT_X, VIDEO_SELECT_Y)
        time.sleep(0.5)
        TestUI.logger.info("Selected Video File({},{})".format(x, y))
        x, y = self.push_button(VIDEO_LOAD_X+10, VIDEO_LOAD_Y)
        time.sleep(0.5)

        TestUI.logger.info("Pushed Video Load({},{})".format(x, y))
        video_mode = TestUI.smmgr.is_video_mode()
        TestUI.logger.info("Selected Video Mode: {}".format(video_mode))
        self.assertTrue(video_mode)

        evfn = str(getVideoDir()/"胃＿ダヴィンチ＿膵上縁25シーン＿結合組織用_0_60.mp4")
        changed, vfn = TestUI.smmgr.get_input_fn()
        TestUI.logger.info("Selected Video File: Expected:{} Result:{}".format(evfn, vfn))
        self.assertEqual(evfn, vfn)

        etf = 1800
        tf = TestUI.smmgr.get_total_frame()
        TestUI.logger.info("Video Total Frame: Expected:{} Result:{}".format(etf, tf))
        self.assertEqual(1800, etf)

        efps = 30
        fps = TestUI.smmgr.get_fps()
        TestUI.logger.info("Video FPS: {}".format(fps))
        TestUI.logger.info("Video FPS: Expected:{} Result:{}".format(efps, fps))

        pause = TestUI.smmgr.is_pause()
        TestUI.logger.info("Video Pause: Expected:{} Result:{}".format(False, pause))
        self.assertFalse(pause)

        x, y = self.push_button(PLAY_PAUSE_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        pause = TestUI.smmgr.is_pause()
        TestUI.logger.info("Pushed Pause Button({},{}) Expected:{} Result:{}".format(x, y, True, pause))
        self.assertTrue(pause)

        esf = 0
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Video Start Frame: Expected:{} Result:{}".format(esf, sf))
        self.assertEqual(esf, sf)

        esf = 500
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 1000
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 1500
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)
        
        esf = 1500
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 1500-10*fps
        x, y = self.push_button(FB_10SEC_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB 10sec Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 1000
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 500
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 0
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 10*fps
        x, y = self.push_button(FF_10SEC_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF 10sec Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        x, y = self.push_button(CHAPTER_X, VIDEO_CTRL_Y)
        TestUI.logger.info("Pushed Chapter Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        esf = 500
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 300
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        x, y = self.push_button(CHAPTER_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        TestUI.logger.info("Pushed Chapter Remove Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 0
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 500
        x, y = self.push_button(FAST_FORWARD_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FF Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        esf = 0
        x, y = self.push_button(FAST_BACK_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        changed, sf = TestUI.smmgr.get_start_frame()
        TestUI.logger.info("Pushed FB Button({},{}) Expected:{} Result:{}".format(x, y, esf, sf))
        self.assertEqual(esf, sf)

        offset = 750
        efi = int(offset / ucds.SLIDER_BAR_WIDTH * tf)
        y = TestUI.calc_ypos(REVIEW_BAR_Y)
        ag.moveTo(REVIEW_BAR_START_X, y, duration=0.5)
        ag.dragRel(offset+1, 0, duration=1)
        time.sleep(1)
        fi = TestUI.smmgr.get_vframe_index()
        TestUI.logger.info("Drag Review bar({},{}) Expected:{} Result:{}".format(REVIEW_BAR_START_X+offset, y, efi, fi))
        self.assertEqual(efi, fi)

        offset = 1250
        efi = int(offset / ucds.SLIDER_BAR_WIDTH * tf)
        y = TestUI.calc_ypos(REVIEW_BAR_Y)
        ag.moveTo(REVIEW_BAR_START_X+offset+1, y, duration=0.5)
        time.sleep(1)
        ag.click(REVIEW_BAR_START_X+offset+1, y, button="left")
        fi = TestUI.smmgr.get_vframe_index()
        TestUI.logger.info("Click Review bar({},{}) Expected:{} Result:{}".format(REVIEW_BAR_START_X+offset, y, efi, fi))
        self.assertEqual(efi, fi)

        x, y = self.push_button(PLAY_PAUSE_X, VIDEO_CTRL_Y)
        time.sleep(0.5)
        pause = TestUI.smmgr.is_pause()
        TestUI.logger.info("Pushed Start Button({},{}) Expected:{} Result:{}".format(x, y, True, pause))
        self.assertFalse(pause)
        time.sleep(1)

        TestUI.logger.info("test_video_mode completed.")

if __name__ == '__main__':
    unittest.main()