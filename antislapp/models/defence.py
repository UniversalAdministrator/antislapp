import time
import traceback
import cPickle
import web

# data looks like:
# data:
#   sued = True/False
#   accusations:
#     - blah blah X
#     - blah blah Y
#     - blah blah Z
#   defences:
#     0:  # (X)
#       - Truth
#       - Absolute Privilege
#     1:  # (Y)
#       - Fair Comment
#       - Responsible Communication
#     2:  # (Z)
#       - Truth
#       - Absolute Privilege
#


class Defence:
    TABLE='conversations'

    def __init__(self, db, conversation_id):
        """
        :type db: web.DB
        :type conversation_id: basestring
        """
        self.db = db
        self.cid = conversation_id
        qvars = {
            'cid': conversation_id
        }
        rows = self.db.select(Defence.TABLE, what='data', where='conversation_id=$cid', vars=qvars)
        try:
            row = rows.first()
            self.data = cPickle.loads(str(row['data']))
            now = int(time.time())
            self.db.update(Defence.TABLE, where='conversation_id=$cid', vars=qvars, atime=now)
        except:
            traceback.print_exc()
            self.data = {}

    def reset(self):
        self.data = {}

    def save(self):
        pickled_data = cPickle.dumps(self.data)
        now = int(time.time())
        with self.db.transaction():
            self.db.delete(Defence.TABLE, where='conversation_id=$cid', vars={'cid': self.cid})
            self.db.insert(Defence.TABLE, conversation_id=self.cid, data=pickled_data, atime=now)

    def set_sued(self, sued):
        self.data['sued'] = bool(sued)

    def add_accusation(self, accusation):
        if 'accusations' not in self.data:
            self.data['accusations'] = []

        self.data['accusations'].append(accusation)
        return len(self.data['accusations']) - 1

    def get_accusations(self):
        return self.data.get('accusations', [])[:]

    def add_defence(self, accusation_id, defence):
        if 'defences' not in self.data:
            self.data['defences'] = {}
        defences = self.data['defences']

        if accusation_id not in defences:
            defences[accusation_id] = []

        defences[accusation_id].append(defence)

    def get_defences(self):
        defences = self.data.get('defences', {})
        return defences.copy()

    def report(self):
        if self.data.get('sued') is None:
            sued = "may have "
        elif self.data.get('sued') is True:
            sued = "have "
        else:
            sued = "have not "

        details = []
        accusations = self.data.get('accusations', [])
        defences = self.data.get('defences', {})
        for i, acc in enumerate(accusations):
            joined_defences = ", ".join(defences.get(i, []))
            details.append("{}. {} ({})".format(i, acc, joined_defences or 'No plead'))
        summary = "You {sued}been sued. You are accused of (and plead): {details}".format(sued=sued, details=', '.join(details))
        return summary

