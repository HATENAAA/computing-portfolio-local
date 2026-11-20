import tempfile,threading,time,unittest
from pathlib import Path
from app.video_jobs import VideoJobs
from app.detector import Config
class JobTests(unittest.TestCase):
 def manager(self,runner):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
  jobs=VideoJobs(temp.name,runner=runner);self.addCleanup(jobs.close);return jobs
 def wait(self,jobs,job,expected):
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   row=jobs.get(job)
   if row['status'] in expected:return row
   time.sleep(.01)
  self.fail(str(jobs.get(job)))
 def test_progress_and_success_persist(self):
  def runner(source,out,progress,cancelled,**settings):out.mkdir();progress(.5)
  j=self.manager(runner);job=j.create('demo.avi');j.submit(job)
  self.assertEqual(self.wait(j,job,{'completed'})['progress'],1)
  self.assertEqual(j.list()[0]['filename'],'demo.avi')
 def test_selected_parameters_and_original_name_reach_worker(self):
  received={}
  def runner(source,out,**settings):received.update(settings);out.mkdir()
  j=self.manager(runner);job=j.create('original.mp4',Config(edge_ratio=.45,brightness=140));j.submit(job)
  self.wait(j,job,{'completed'})
  self.assertEqual(received['config'].edge_ratio,.45)
  self.assertEqual(received['config'].brightness,140)
  self.assertEqual(received['source_name'],'original.mp4')
 def test_queue_bound_and_queued_cancel(self):
  def runner(source,out,progress,cancelled,**settings):
   while not cancelled():time.sleep(.005)
   raise InterruptedError()
  j=self.manager(runner);first=j.create('a.avi');j.submit(first)
  self.wait(j,first,{'running'});second=j.create('b.avi');j.submit(second);third=j.create('c.avi')
  with self.assertRaises(ValueError):j.create('d.avi')
  j.cancel(second);self.assertEqual(j.get(second)['status'],'cancelled')
  j.cancel(first);self.wait(j,first,{'cancelled'});j.cancel(third)
 def test_running_cancel_cleans_partial_results(self):
  def runner(source,out,progress,cancelled,**settings):
   out.mkdir();(out/'partial.txt').write_text('x')
   while not cancelled():time.sleep(.005)
   raise InterruptedError()
  j=self.manager(runner);job=j.create('a.avi');j.submit(job);self.wait(j,job,{'running'});j.cancel(job)
  self.wait(j,job,{'cancelled'});self.assertFalse((j.root/job/'analysis').exists())
 def test_failure_does_not_publish_partial_outputs(self):
  def runner(source,out,progress,cancelled,**settings):out.mkdir();raise RuntimeError('private path')
  j=self.manager(runner);job=j.create('a.avi');j.submit(job);row=self.wait(j,job,{'failed'})
  self.assertNotIn('private path',row['error']);self.assertFalse((j.root/job/'analysis').exists())
 def test_restart_marks_unfinished_jobs_as_failed(self):
  j=self.manager(lambda *a,**kw:None);job=j.create('a.avi');j.close()
  other=VideoJobs(j.root);self.addCleanup(other.close);self.assertEqual(other.get(job)['status'],'failed')

 def test_retained_source_is_kept_only_after_success(self):
  def runner(source,out,**settings):out.mkdir()
  jobs=self.manager(runner)
  for keep in (True,False):
   job=jobs.create('test.mp4',retain_source=keep);source=jobs.root/job/'source.video';source.write_bytes(b'synthetic upload')
   jobs.submit(job);self.wait(jobs,job,{'completed'});jobs.executor.submit(lambda:None).result(timeout=3)
   self.assertEqual(source.exists(),keep)
  def fail(source,out,**settings):raise ValueError('decode failed')
  failed=self.manager(fail);job=failed.create('bad.mp4',retain_source=True);source=failed.root/job/'source.video';source.write_bytes(b'bad')
  failed.submit(job);self.wait(failed,job,{'failed'});failed.executor.submit(lambda:None).result(timeout=3);self.assertFalse(source.exists())
