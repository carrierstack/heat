#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Client Library for Marconi Resources."""

from heat.engine import clients
from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)

try:
    from marconiclient.queues.v1 import client as marconiclient
except ImportError:
    marconiclient = None


class Clients(clients.OpenStackClients):

    def _marconi(self, service_type="queuing"):

        con = self.context
        if self.auth_token is None:
            LOG.error(_("Marconi connection failed, no auth_token!"))
            return None

        opts = {
            'os_auth_token': con.auth_token,
            'os_auth_url': con.auth_url,
            'os_project_id': con.tenant,
            'os_service_type': service_type,
        }
        auth_opts = {'backend': 'keystone',
                     'options': opts}
        conf = {'auth_opts': auth_opts}
        endpoint = self.url_for(service_type=service_type)

        return marconiclient.Client(url=endpoint, conf=conf)
