import unittest
from Play.play import *
from datetime import datetime
from sharedmemory import SharedMemoryManager
from utils.utils import getVideoDir
from multiprocessing import Process
import time

class TestPlay(unittest.TestCase):

    def run_play(boot_timestamp: datetime, smmgr: SharedMemoryManager) -> None:
        '''Playサブプロセス
        @param  boot_timestamp  最初にログ出力するタイムスタンプ
        @param  smmgr           共有メモリマネージャ
        '''
        from Play.play import Play
        Play(boot_timestamp, smmgr).run()

    def setUpClass():
        print("setUpClass:: started.")

        TestPlay.boot_timestamp = datetime.now()
        TestPlay.smmgr = SharedMemoryManager()

        raw_image = cuda.mem_alloc(1920 * 1080 * 3)
        TestPlay.smmgr.raw_image_handle[:] = cuda.mem_get_ipc_handle(raw_image)
        TestPlay.smmgr.raw_image_initialized.value = True

        TestPlay.process = Process(target=TestPlay.run_play, args=[TestPlay.boot_timestamp, TestPlay.smmgr])
        TestPlay.process.start()

    def tearDownClass():
        print("tearDownClass:: started.")

    def setUp(self):
        print("setUp:: started.")

    def tearDown(self):
        print("tearDown:: started.")

    def test_open_video(self):
        input = str(getVideoDir()/"胃＿ダヴィンチ＿膵上縁25シーン＿結合組織用_0_60.mp4")
        TestPlay.smmgr.set_input_fn(input)
        time.sleep(0.5)

        self.assertAlmostEqual(30.0, TestPlay.smmgr.get_fps())
        self.assertEqual(1800, TestPlay.smmgr.get_total_frame())

    def test_start_frame(self):
        esf = 1200
        TestPlay.smmgr.set_start_frame(esf)
        time.sleep(2)

