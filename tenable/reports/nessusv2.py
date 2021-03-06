from lxml import etree
import dateutil.parser, time


class NessusReportv2(object):
    '''
    The NessusReport generator will return vulnerability items from any
    Nessus version 2 formatted Nessus report file.  The returned data will be
    a python dictionary representation of the ReportItem with the relevent
    host properties attached.  The ReportItem's structure itself will determine
    the resulting dictionary, what attributes are returned, and what is not.

    Args:
        fobj (File object or string path):
            Either a File-like object or a string path pointing to the file to
            be parsed.
    '''
    def __init__(self, fobj):
        self._iter = etree.iterparse(fobj, events=('start', 'end'))

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def _defs(self, name, value):
        if name in ['cvss_vector', 'cvss_temporal_vector']:
            # Return a list of the Vectors instead of having everything in a
            # flat string.  This should allow for much easier parsing later.
            return value.split('/')

        elif name in ['cvss_base_score', 'cvss_temporal_score']:
            # CVSS scores are floats, so lets return them as such.
            return float(value)

        elif name in ['first_found', 'last_found', 'plugin_modification_date',
                      'plugin_publication_date', 'HOST_END', 'HOST_START']:
            # The first and last found attributes use a datetime timestamp
            # format that we should convert into a unix timestamp.
            return dateutil.parser.parse(value)

        elif name in ['port', 'pluginID', 'severity']:
            return int(value)

        else:
            return value

    def next(self):
        '''
        Get the next ReportItem from the nessus file and return it as a
        python dictionary.  

        Generally speaking this method is not called directly, but is instead
        called as part of a loop.

        Examples:
            For example, if we wanted to load a Nessus report from disk and
            iterate through the contents, it would simply be a matter of:

            >>> with open('example.nessus') as nessus_file:
            ...     report = NessusReportv2(nessus_file)
            ...     for item in report:
            ...         print(item) 
        '''
        try:
            for event, elem in self._iter:
                if event == 'start' and elem.tag == 'ReportHost':
                    # If we detect a new ReportHost, then we will want to rebuild
                    # the host information cache, starting with the ReportHost's
                    # name for the host.
                    self._cache = {'host-report-name': elem.get('name')}

                if event == 'end' and elem.tag == 'HostProperties':
                    # Once we have finished parsing out all of the host properties,
                    # we need to update the host cache with this new information.
                    for child in elem.getchildren():
                        self._cache[child.get('name')] = child.text
                    elem.clear()

                if event == 'end' and elem.tag == 'ReportHost':
                    # If we reach the end of the ReportHost tree, then clear out
                    # the element.
                    elem.clear()
                if event == 'end' and elem.tag == 'NessusClientData_v2':
                    # If we reach the end of the Nessus file, then we need to raise
                    # a StopIteration exception to inform the code downstream that
                    # we have reached the end of the file.
                    raise StopIteration()

                if event == 'end' and elem.tag == 'ReportItem':
                    # Once we have finished gathering all of the information for a
                    # ReportItem, lets go ahead and parse out the ReportItem, graft
                    # on the cached HostProperties that we gathered before, and then
                    # return the data as a python dictionary.
                    vuln = dict(elem.attrib)
                    vuln.update(self._cache)

                    # all of the information we have passed into the vuln dictionary
                    # needs to be normalized.  Here we will pass each item through
                    # the definition parser to make sure any known values are
                    # formatted properly.
                    for k in vuln.keys():
                        vuln[k] = self._defs(k, vuln[k])

                    for c in elem.getchildren():
                        # iterate through each child element and add it to the vuln
                        # dictionary.  We will also check to see if we have seen
                        # the tag before, and if so, convert the stored value to a 
                        # list of values.  The need to return a list is common for
                        # things like CVEs, BIDs, See-Alsos, etc.

                        if c.tag in vuln:
                            if not isinstance(vuln[c.tag], list):
                                vuln[c.tag] = [vuln[c.tag],]
                            vuln[c.tag].append(self._defs(c.tag, c.text))
                        else:
                            vuln[c.tag] = self._defs(c.tag, c.text)

                    # Clear out the element from the element tree and return the
                    # vuln dictionary.
                    elem.clear()
                    return vuln
        except TypeError as err:
            if err.args[0] == 'reading file objects must return bytes objects':
                raise TypeError('File object not opened in binary mode.')
            else:
                raise err
