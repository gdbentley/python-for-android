# -------------------------------------------------------------------
# Broadcast receiver bridge

from jnius import autoclass, PythonJavaClass, java_method

class BroadcastReceiver(object):

    class Callback(PythonJavaClass):
        __javainterfaces__ = ['org/renpy/android/GenericBroadcastReceiverCallback']
        __javacontext__ = 'app'

        def __init__(self, callback, *args, **kwargs):
            self.callback = callback
            PythonJavaClass.__init__(self, *args, **kwargs)

        @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
        def onReceive(self, context, intent):
            self.callback(context, intent)

    def __init__(self, callback, actions=None, categories=None):
        super(BroadcastReceiver, self).__init__()
        self.callback = callback

        if not actions and not categories:
            raise Exception('You need to define at least actions or categories')

        def _expand_partial_name(partial_name):
            if '.' in partial_name:
                return partial_name # Its actually a full dotted name
            else:
                name = 'ACTION_{}'.format(partial_name.upper())
                if not hasattr(Intent, name):
                    raise Exception('The intent {} doesnt exist'.format(name))
                return getattr(Intent, name)

        # resolve actions/categories first
        Intent = autoclass('android.content.Intent')
        resolved_actions = [_expand_partial_name(x) for x in actions or []]
        resolved_categories = [_expand_partial_name(x) for x in categories or []]

        # resolve android API
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        GenericBroadcastReceiver = autoclass('org.renpy.android.GenericBroadcastReceiver')
        IntentFilter = autoclass('android.content.IntentFilter')
        HandlerThread = autoclass('android.os.HandlerThread')

        # create a thread for handling events from the receiver
        self.handlerthread = HandlerThread('handlerthread')

        # create a listener
        self.context = PythonActivity.mActivity
        self.listener = BroadcastReceiver.Callback(self.callback)
        self.receiver = GenericBroadcastReceiver(self.listener)
        self.receiver_filter = IntentFilter()
        for x in resolved_actions:
            self.receiver_filter.addAction(x)
        for x in resolved_categories:
            self.receiver_filter.addCategory(x)

    def start(self):
        Handler = autoclass('android.os.Handler')
        self.handlerthread.start()
        self.handler = Handler(self.handlerthread.getLooper())
        self.context.registerReceiver(self.receiver, self.receiver_filter, None,
                self.handler)

    def stop(self):
        self.context.unregisterReceiver(self.receiver)
        self.handlerthread.quit()


