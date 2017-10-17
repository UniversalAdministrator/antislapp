import os
import web
import json
import pprint
import traceback
import antislapp.index
from antislapp.models.defence import Defence


class Fulfill:
    outfile = os.path.join(antislapp.index.BASE_FOLDER, 'sessions', 'test.txt')

    def __init__(self):
        pass

    def dump_error(self, data, response):
        with file(Fulfill.outfile, 'w') as f:
            f.write("\n==== error ====\n")
            er = traceback.format_exc()
            f.write(er)
            f.write("\n==== data ====\n")
            try:
                pprint.pprint(json.loads(data), f)
            except:
                f.write("(json decode failed)\n")
                pprint.pprint(data, f)
            f.write("\n==== response ====\n")
            pprint.pprint(response, f)
            f.write("\n==== end ====\n")

    @staticmethod
    def extract_parameters(data):
        params = data.get('result', {}).get('parameters', {})
        for key in params:
            if params[key].lower() == 'false':
                params[key] = False
            elif params[key].lower() == 'true':
                params[key] = True
        return params

    @staticmethod
    def extract_default_response(data):
        return data.get('result', {}).get('fulfillment', {}).get('speech', "")

    @staticmethod
    def extract_action(data):
        return data.get('result', {}).get('action', '')

#    @staticmethod
#    def extract_context(data):
#        pass

    @staticmethod
    def join_list(items):
        l = len(items)
        if l == 0:
            joined = ''
        elif l == 1:
            joined = items[0]
        elif l == 2:
            joined = "{} and {}".format(*items)
        else:
            joined = "{}, and {}".format(", ".join(items[:-1]), items[-1])
        return joined

    @staticmethod
    def summarize(params):
        if params.get('sued', False):
            sued = 'you have been sued'
        else:
            sued = "you have not been sued"

        if params.get('truth', False):
            if params.get('truth-evidence'):
                truth = "your words were true and you have some proof"
            else:
                truth = "your words were true but you have no proof"
        else:
            truth = "your words were untrue"

        if 'absolute' in params:
            if params['absolute']:
                if params.get('abspriv', False):
                    absolute = 'you were in a position of absolute privilege'
                else:
                    absolute = 'you were in a position of privilege but repeated yourself after the privilege ended'
            else:
                absolute = "you weren't in a position of absolute privilege"
        else:
            absolute = None

        if 'qualified' in params:
            if params['qualified']:
                qualified = 'you were in a position of qualified privilege'
            else:
                qualified = "you weren't in a position of qualified privilege"
        else:
            qualified = None

        if 'comment' in params:
            if params['comment']:
                comment = 'you were expressing your opinion on a matter of public interest'
            else:
                comment = "it didn't qualify as fair comment"
        else:
            comment = None

        if 'journalist' in params:
            if params['journalist']:
                journalist = 'you were commenting on an urgent matter of public interest'
            else:
                journalist = 'you didn\'t qualify for "Responsible Communication" defence.'
        else:
            journalist = None

        points = [sued, truth, absolute, qualified, comment, journalist]
        points = [p for p in points if p]
        summary = "So, to summarize: {}".format(Fulfill.join_list(points))
        return summary

    def decode_inbound(self, inbound):
        try:
            data = json.loads(inbound)
        except:
            data = {}
        params = Fulfill.extract_parameters(data)
        def_response = Fulfill.extract_default_response(data)
        action = Fulfill.extract_action(data)
        cid = data.get('sessionId', None)
        if cid is None:
            raise ValueError

        request = {
            'db': antislapp.index.db,
            'params': params,
            'default': def_response,
            'action': action,
            'conversation_id': cid,
        }
        return request

    def process_request(self, request):
        defence = Defence(request['db'], request['conversation_id'])

        response = {
            'speech': request['default'],
            'displayText': request['default'],
        }

        if request['action'] == "is_sued":
            defence.set_sued(request['params'].get('sued', False))
        elif request['action'] == 'get_accusations':
            pass
        elif request['action'] == 'done_accusations':
            pass
        elif request['action'] == 'defence':
            pass
        else:
            pass

        defence.save()
        return response

    def prepare_response(self, response):
        prepared = {
            'speech': response['speech'],  # String. Response to the request.
            'displayText': response['displayText'],  # String. Text displayed by client.
            'data': response.get('data', ''),  # Object. this data is passed through DialogFlow and sent to the client.
            'contextOut': response.get('contextOut', []),  # Array of context objects. Output context for the current intent.
            # eg: [{"name":"weather", "lifespan":2, "parameters":{"city":"Rome"}}]
            'source': response.get('source', 'riobot'),  # String. Data source (??)
            'followupEvent': response.get('event', {})  # Object. Event name and optional parameters sent from the web service to Dialogflow.
            # eg: {"name":"<event_name>","data":{"<parameter_name>":"<parameter_value>"}}
        }
        return prepared


    def POST(self):
        inbound = web.data()

        request = self.decode_inbound(inbound)
        response = self.process_request(request)
        outbound = self.prepare_response(response)

        # use action and params to determine current phase of conversation
        # save relevant params.
        # choose event to trigger (if needed)
        # adjust output speech/displayText? (if needed?)

        self.dump_error(inbound, outbound)
        web.header("Content-Type", "application/json")
        return json.dumps(response)
