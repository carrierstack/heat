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

from heat.common import exception
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.openstack.common import log as logging

from .. import clients  # noqa


LOG = logging.getLogger(__name__)


class Order(resource.Resource):

    PROPERTIES = (
        NAME, PAYLOAD_CONTENT_TYPE, MODE, EXPIRATION,
        ALGORITHM, BIT_LENGTH,
    ) = (
        'name', 'payload_content_type', 'mode', 'expiration',
        'algorithm', 'bit_length',
    )

    ATTRIBUTES = (
        STATUS, ORDER_REF, SECRET_REF,
    ) = (
        'status', 'order_ref', 'secret_ref',
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Human readable name for the secret.'),
        ),
        PAYLOAD_CONTENT_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('The type/format the secret data is provided in.'),
            default='application/octet-stream',
            constraints=[
                constraints.AllowedValues([
                    'application/octet-stream',
                ]),
            ],
        ),
        EXPIRATION: properties.Schema(
            properties.Schema.STRING,
            _('The expiration date for the secret in ISO-8601 format.'),
            constraints=[
                constraints.CustomConstraint('iso_8601'),
            ],
        ),
        ALGORITHM: properties.Schema(
            properties.Schema.STRING,
            _('The algorithm type used to generate the secret.'),
            default='aes',
            constraints=[
                constraints.AllowedValues([
                    'aes',
                ]),
            ],
        ),
        BIT_LENGTH: properties.Schema(
            properties.Schema.NUMBER,
            _('The bit-length of the secret.'),
            constraints=[
                constraints.AllowedValues([
                    128,
                    196,
                    256,
                ]),
            ],
        ),
        MODE: properties.Schema(
            properties.Schema.STRING,
            _('The type/mode of the algorithm associated with the secret '
              'information.'),
            default='cbc',
            constraints=[
                constraints.AllowedValues([
                    'cbc',
                ]),
            ],
        ),
    }

    attributes_schema = {
        STATUS: attributes.Schema(_('The status of the order.')),
        ORDER_REF: attributes.Schema(_('The URI to the order.')),
        SECRET_REF: attributes.Schema(_('The URI to the created secret.')),
    }

    def __init__(self, name, json_snippet, stack):
        super(Order, self).__init__(name, json_snippet, stack)
        self.clients = clients.Clients(self.context)

    def barbican(self):
        return self.clients.client('barbican')

    def handle_create(self):
        info = dict(self.properties)
        order_ref = self.barbican().orders.create(**info)
        self.resource_id_set(order_ref)
        return order_ref

    def check_create_complete(self, order_href):
        order = self.barbican().orders.get(order_href)

        if order.status == 'ERROR':
            reason = order.error_reason
            code = order.error_status_code
            msg = (_("Order '%(name)s' failed: %(code)s - %(reason)s")
                   % {'name': self.name, 'code': code, 'reason': reason})
            raise exception.Error(msg)

        return order.status == 'ACTIVE'

    def handle_delete(self):
        if not self.resource_id:
            return

        try:
            self.barbican().orders.delete(self.resource_id)
            self.resource_id_set(None)
        except clients.barbican_client.HTTPClientError as exc:
            # This is the only exception the client raises
            # Inspecting the message to see if it's a 'Not Found'
            if 'Not Found' in str(exc):
                self.resource_id_set(None)
            else:
                raise

    def _resolve_attribute(self, name):
        try:
            order = self.barbican().orders.get(self.resource_id)
        except clients.barbican_client.HTTPClientError as exc:
            LOG.warn(_("Order '%(name)s' not found: %(exc)s") %
                     {'name': self.resource_id, 'exc': str(exc)})
            return ''

        return getattr(order, name)


def resource_mapping():
    return {
        'OS::Barbican::Order': Order,
    }


def available_resource_mapping():
    if not clients.barbican_client:
        return {}

    return resource_mapping()
