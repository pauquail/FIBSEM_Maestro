import logging

from fibsem_maestro.tools.email_attention import send_email


class ErrorHandler:
    def __init__(self, settings, stopping_flag):
        self._settings_init(settings['general']['error_behaviour'], settings['email'])
        self.stopping_flag = stopping_flag

    def _settings_init(self, error_behaviour_settings, email_settings):
        self.error_behaviour_settings = error_behaviour_settings
        self.sender = email_settings['sender']
        self.receiver = email_settings['receiver']
        self.password_file = email_settings['password_file']

    def settings_init(self, settings):
        """ For global re-initialization of settings  (global settings always passed)"""
        self._settings_init(settings['general']['error_behaviour'], settings['email'])

    def __call__(self, exception):
        if 'email' in self.error_behaviour_settings:
            try:
                send_email(self.sender, self.receiver, 'Maestro - acquisition error', repr(exception),
                           password_file=self.password_file)
            except Exception as e:
                logging.error('Email sending error! ' + repr(e))
        if 'stop' in self.error_behaviour_settings:
            self.stopping_flag.stopping_flag = True
        if 'exception' in self.error_behaviour_settings:
            raise RuntimeError('Acquisition error! ' + repr(exception))