import unittest
from app.temporal import event_metrics,RollingEventGate

class EventErrorTests(unittest.TestCase):
    def test_error_taxonomy_and_conservation(self):
        truth=[dict(start=1,end=3),dict(start=10,end=12)]
        pred=[dict(start=1,end=3),dict(start=1,end=3),dict(start=2.9,end=4),dict(start=20,end=21)]
        r=event_metrics(pred,truth)
        self.assertEqual((r['tp'],r['fp'],r['fn']),(1,3,1))
        self.assertEqual(r['error_counts'],dict(duplicate=1,temporal_localisation=1,background=1))
        self.assertEqual(r['missed_truth_indices'],[1])
        self.assertEqual(len(r['matched_pairs'])+len(r['false_positives']),len(pred))
    def test_maximum_matching_beats_greedy(self):
        # Broad prediction can match either truth, narrow one can match only the first.
        r=event_metrics([dict(start=0,end=4),dict(start=0,end=2)],
                        [dict(start=0,end=2),dict(start=2,end=4)],.5)
        self.assertEqual(r['tp'],2)
        self.assertEqual(r['missed_truth_indices'],[])
    def test_empty_annotations_and_predictions(self):
        self.assertIsNone(event_metrics([],[])['precision'])
        r=event_metrics([dict(start=0,end=1)],[])
        self.assertEqual(r['error_counts']['background'],1)
    def test_rejected_frame_does_not_poison_rolling_votes(self):
        a,b=RollingEventGate(2),RollingEventGate(2)
        for gate in [a,b]:gate.update(0,True)
        with self.assertRaises(ValueError):a.update(0,True)
        with self.assertRaises(ValueError):a.update(.1,1)
        for gate in [a,b]:gate.update(.2,False);gate.update(.4,True)
        self.assertEqual(a.finish(),b.finish())

if __name__=='__main__':unittest.main()
