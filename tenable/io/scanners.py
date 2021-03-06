from .base import TIOEndpoint

class ScannersAPI(TIOEndpoint):

    @property
    def linking_key(self):
        '''
        The linking key for the Tenable.io instance.
        '''
        scanners = self.list()
        for scanner in scanners:
            if scanner['uuid'] == '00000000-0000-0000-0000-00000000000000000000000000001':
                return scanner['key']

    def allowed_scanners(self):
        '''
        A simple convenience function that returns the list of scanners that the
        current user is allowed to use.

        Returns:
            list: List of scanner documents.
        '''
        # We want to get the scanners that are avilable for scanning.  To do so,
        # we will want to pull the information from the scan template.  This
        # isn't the prettiest way to handle this, however it will consistently
        # return the results that we are looking for.
        def get_scanners(tmpl):
            for item in tmpl['settings']['basic']['inputs']:
                if item['id'] == 'scanner_id':
                    return item['options']

        vm_tmpl = self._api.policies.templates()['advanced']
        was_tmpl = self._api.policies.templates()['was_scan']
        vm_scanners = get_scanners(self._api.editor.details('scan', vm_tmpl))
        was_scanners = get_scanners(self._api.editor.details('scan', was_tmpl))
        return vm_scanners + was_scanners

    def control_scan(self, scanner_id, scan_uuid, action):
        '''
        `scanners: control-scans <https://cloud.tenable.com/api#/resources/scanners/control-scans>`_

        Args:
            scanner_id (int):
                The unique identifier for the scanner.
            scan_uuid (uuid):
                The unique identifier for the scan.
            action (str):
                The action to take upon the scan.  Valid actions are `stop`,
                `pause`, and `resume`.

        Returns:
            None: The action was sent to the scan successfully.
        '''
        self._api.post('scanners/{}/scans/{}/control'.format(
            self._check('scanner_id', scanner_id, int),
            self._check('scan_uuid', scan_uuid, str),
            ), json={'action': self._check('action', action, str, 
                                        choices=['stop', 'pause', 'resume'])})

    def delete(self, id):
        '''
        `scanners: delete <https://cloud.tenable.com/api#/resources/scanners/delete>`_

        Args:
            id (int):
                The unique identifier for the scanner to delete.

        Returns:
            None: The scanner was successfully deleted.
        '''
        self._api.delete('scanners/{}'.format(self._check('id', id, int)))

    def details(self, id):
        '''
        `scanners: details <https://cloud.tenable.com/api#/resources/scanners/details>`_

        Args:
            id (int):
                The unique identifier for the scanner

        Returns:
            dict: The scanner resource record.
        '''
        return self._api.get('scanners/{}'.format(
            self._check('id', id, int))).json()

    def edit(self, id, **kwargs):
        '''
        `scanners: edit <https://cloud.tenable.com/api#/resources/scanners/edit>`_

        Args:
            id (int):
                The unique identifier for the scanner.
            force_plugin_update (bool, optional):
                Force the scanner to perform a plugin update .
            force_ui_update (bool, optional):
                Force the scanner to perform a UI update.
            finish_update (bool, optional):
                Force the scanner to reboot to complete the update process.
                This action is only valid when automatic updates are disabled.
            registration_code (str, optional):
                Sets the registration code for the scanner.
            aws_update_interval (int, optional):
                For AWS scanners this will inform the scanner how often to check
                into Tenable.io.

        Returns:
            None: The operation was requested successfully.
        '''
        payload = dict()
        if ('force_plugin_update' in kwargs 
            and self._check('force_plugin_update', kwargs['force_plugin_update'], bool)):
            payload['force_plugin_update'] = 1
        if ('force_ui_update' in kwargs
            and self._check('force_ui_update', kwargs['force_ui_update'], bool)):
            payload['force_ui_update'] = 1
        if ('finish_update' in kwargs
            and self._check('finish_update', kwargs['finish_update'], bool)):
            payload['finish_update'] = 1
        if ('registration_code' in kwargs
            and self._check('registration_code', kwargs['registration_code'], str)):
            payload['registration_code'] = kwargs['registration_code']
        if ('aws_update_interval' in kwargs
            and self._check('aws_update_interval', kwargs['aws_update_interval'], int)):
            payload['aws_update_interval'] = kwargs['aws_update_interval']

        self._api.put('settings/{}'.format(self._check('id', id, int)), 
            json=payload)

    def get_aws_targets(self, id):
        '''
        `scanners: get-aws-targets <https://cloud.tenable.com/api#/resources/scanners/get-aws-targets>`_

        Args:
            id (int): The unique identifier for the scanner.

        Returns:
            list: List of aws target resource records.
        '''
        return self._api.get('scanners/{}/aws-targets'.format(
                    self._check('id', id, int))).json()['targets']

    def get_scanner_key(self, id):
        '''
        `scanners: get-scanner-key <https://cloud.tenable.com/api#/resources/scanners/get-scanner-key>`_

        Args:
            id (int): The unique identifier for the scanner.

        Returns:
            str: The scanner key
        '''
        return str(self._api.get('scanners/{}/key'.format(
            self._check('id', id, int))).json()['key'])

    def get_scans(self, id):
        '''
        `scanners: get-scans <https://cloud.tenable.com/api#/resources/scanners/get-scans>`_

        Args:
            id (int): The unique identifier for the scanner.

        Returns:
            list: List of scan resource records associated ot the scanner.
        '''
        return self._api.get('scanners/{}/scans'.format(
            self._check('id', id, int))).json()['scans']

    def list(self):
        '''
        `scanners: list <https://cloud.tenable.com/api#/resources/scanners/list>`_

        Returns:
            list: List of scanner resource records.
        '''
        return self._api.get('scanners').json()['scanners']

    def toggle_link_state(self, id, linked):
        '''
        `scanners: toggle-link-state <https://cloud.tenable.com/api#/resources/scanners/toggle-link-state>`_

        Args:
            id (int): The unique identifier for the scanner
            linked (bool): 
                The link status of the scanner.  Setting to `False` will disable
                the link, whereas seting to `True` will enable the link.

        Returns:
            None: The status change was successful.
        '''
        self._api.put('scanners/{}/link'.format(self._check('id', id, int)), 
            json={'link': int(self._check('linked', linked, bool))})