odoo.define('enterprise_disable_expire.ExpirationPanel', function (require) {
    let HomeMenu = require('web_enterprise.HomeMenu');

    let DisableExpireHomeMenu = HomeMenu.include({
        _enterpriseExpirationCheck: function () {
            return;
        }
    })
})
