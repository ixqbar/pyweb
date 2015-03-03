
App = {
    'connected' : false,
    'pub_data'  : {
        'pub_id'             : 0,
        'pub_config_version' : '',
        'pub_game_version'   : '',
        'pub_desc'           : '',
        'pub_status'         : 'zip',
        'pub_servers'        : []
    },
    'servers' : {}
}

App.log = function(message) {
    if (typeof message == 'object') {
        console.dir(message)
    } else {
        console.log(message)
    }
}

App.debug = function(message) {
    console.group('debug info')
    console.log(message)
    console.groupEnd()
}

App.init = function(pub_data) {
    this.pub_data = $.extend(this.pub_data, pub_data);
    this.debug(this.pub_data);

    return this;
}

App.run = function() {
    this.initHtml();
    this.runSocket();
    this.zipBind();

    return this;
}

App.initHtml = function() {
    $('#zip_config_version').val(this.pub_data.pub_config_version);
    $('#zip_game_version').val(this.pub_data.pub_game_version);
    $('#zip_desc').val(this.pub_data.pub_desc);
}

App.runSocket = function() {
    var _this = this;
    this.ws = new WebSocket("ws://127.0.0.1:8888/socket")
    this.ws.onopen = function() {
        _this.connected = true;
        _this.debug('connected server')
        _this.loadServers();
    }
    this.ws.onclose = function(event) {
        _this.connected = false;
        _this.debug('server disconnected code=' + event.code + ',reason=' + event.reason)
    }
    this.ws.onmessage = function(event) {
        if (0 == event.data.length) {
            return;
        }

        var response = JSON.parse(event.data)
        if (typeof response.executor == 'undefined'
            || typeof response.params == 'undefined') {
            return;
        }

        var executor = response.executor
        try {
            if (0 == executor.length || typeof executor != 'string') executor = 'log';
            executor = eval('_this.' + executor);
            if (0 == response.params.length) {
                executor.call(_this);
            } else {
                executor.call(_this, response.params);
            }
        } catch (e) {
            _this.log(e);
        }
    }

    //to fixed websocket interrupted while page was loading in Fireox and Chrome
    $(window).on('beforeunload', function(){
        _this.ws.close();
    });
}

App.loadServers = function() {
    this.socketSend({
        'action' : 'servers',
        'params' : {},
        'callback' : 'loadServersExecutor'
    });
}

App.loadServersExecutor = function(servers) {
    this.debug(servers);
    this.servers = servers;
    var _html = ['<input type="checkbox" id="servers_all" value="" /> ALL<br/>'];
    for (var i in servers) {
        if ($.inArray(servers[i].server_id + '', this.pub_data.pub_servers) >= 0) {
            _html.push('<input type="checkbox" value="' + servers[i].server_id + '" checked/>' + servers[i].server_name)
        } else {
            _html.push('<input type="checkbox" value="' + servers[i].server_id + '" />' + servers[i].server_name)
        }
    }

    $('#servers_op').html(_html.join(''));

    if (1 == _html.length) {
        $('#servers_all').attr('disabled', 'disabled');
    } else {
        if (this.pub_data.pub_status == 'zip'
            || this.pub_data.pub_status == 'zip_success') {
            $('#servers_all').click(function () {
                var checkboxes = $('#servers_op').find(':checkbox');
                if ($(this).is(':checked')) {
                    checkboxes.prop('checked', true);
                } else {
                    checkboxes.prop('checked', false);
                }
            });
        } else {
            $('#servers_op').find(':checkbox').attr('disabled', 'disabled');
        }
    }
}

App.socketSend = function(message) {
    if (false == this.connected) {
        this.debug('not connected server');
        return;
    }

    if (typeof message != 'object') {
        this.debug('error send message type')
        return;
    }

    this.ws.send(JSON.stringify(message))
}

App.zipBind = function() {
    if (this.pub_data.pub_id > 0 && this.pub_data.pub_status != 'zip') {
        $('#btn-zip').off('click');
        $('#btn-zip').attr('disabled', 'disabled');
        $('#btn-zip').removeClass('btn-info');
        $('#btn-zip').text('Finished zip');
        $('#servers').show();

        $('#zip_config_version').attr('disabled', 'disabled');
        $('#zip_game_version').attr('disabled', 'disabled');
        $('#zip_desc').attr('disabled', 'disabled');

        $('#pub_result').append('<h5> · zip finished (pub id=' + this.pub_data.pub_id + ')</h5>');

        this.sycBind();

        return;
    }

    var _this = this;
    $('#btn-zip').click(function(){
        var _zip_config_version = $('#zip_config_version').val();
        var _zip_game_version   = $('#zip_game_version').val();
        var _zip_desc           = $('#zip_desc').val();

        if (0 == _zip_config_version.length) {
            $('#zip_config_version').css({"border":"2px solid red"});
            $('#zip_config_version').attr('placeholder', 'Please type config version');
            return;
        } else {
            $('#zip_config_version').css({"border":""});
        }

        if (0 == _zip_game_version.length) {
            $('#zip_game_version').css({"border":"2px solid red"});
            $('#zip_game_version').attr('placeholder', 'Please type game version');
            return;
        } else {
            $('#zip_game_version').css({"border":""});
        }

        if (0 == _zip_desc.length) {
            $('#zip_desc').css({"border":"2px solid red"});
            $('#zip_desc').attr('placeholder', 'Please type a description for your publish');
            return;
        } else {
            $('#zip_desc').css({"border":""});
        }

        $('#zip_config_version').attr('disabled', 'disabled');
        $('#zip_game_version').attr('disabled', 'disabled');
        $('#zip_desc').attr('disabled', 'disabled');

        $(this).off('click');
        $(this).attr('disabled', 'disabled');
        $(this).removeClass('btn-info');
        $(this).text('Waiting ...');

        _this.pub_data.pub_config_version = _zip_config_version;
        _this.pub_data.pub_game_version   = _zip_game_version;
        _this.pub_data.pub_desc           = _zip_desc;
        _this.pub_data.pub_id             = _this.pub_data.pub_id;

        _this.zipExecute();
    });
}

App.sycBind = function() {
    if (this.pub_data.pub_id > 0
        && (this.pub_data.pub_status == 'syc_success'
            || this.pub_data.pub_status == 'pub'
            || this.pub_data.pub_status == 'pub_success')) {
        $('#btn-syc').off('click');
        $('#btn-syc').attr('disabled', 'disabled');
        $('#btn-syc').removeClass('btn-info');
        $('#btn-syc').text('Finished syc');

        $('#pub_result').append('<h5> · sync all finished</h5>');

        this.pubBind();

        return;
    }

    $('#btn-syc').removeAttr('disabled');
    $('#btn-syc').addClass('btn-info');

    var _this = this;
    $('#btn-syc').click(function(){
        if (_this.pub_data.pub_id <= 0) {
            _this.debug('Unknown pub_id');
            return
        }

        _this.pub_data.pub_servers.length = []
        $("input[type='checkbox']:checked").each(function() {
            _this.pub_data.pub_servers.push($(this).val());
        });

        _this.debug(_this.pub_data.pub_servers);

        if (0 == _this.pub_data.pub_servers.length) {
            $('#servers_op').css({"border":"2px solid red"});
            return;
        } else {
            $('#servers_op').css({"border":""});
        }

        $('#servers_op').find(':checkbox').attr('disabled', 'disabled');

        $(this).off('click');
        $(this).attr('disabled', 'disabled');
        $(this).removeClass('btn-info');
        $(this).text('Waiting ...');

        _this.sycExecute();
    });
}

App.pubBind = function() {
    $('#btn-pub').removeAttr('disabled');
    $('#btn-pub').addClass('btn-info');

    var _this = this;

    $('#btn-pub').click(function(){
        if (_this.pub_data.pub_id <= 0) {
            _this.debug('Unknown pub_id');
            return
        }

        $(this).off('click');
        $(this).attr('disabled', 'disabled');
        $(this).removeClass('btn-info');
        $(this).text('Waiting ...');

        _this.pubExecute();
    });
}

App.zipExecute = function() {
    this.socketSend({
        'action' : 'to_zip',
        'params' : {
            'config_version' : this.pub_data.pub_config_version,
            'game_version'   : this.pub_data.pub_game_version,
            'desc'           : this.pub_data.pub_desc,
            'pub_id'         : this.pub_data.pub_id
        },
        'callback' : 'executeResponse'
    });
}

App.sycExecute = function () {
    this.socketSend({
        'action' : 'to_syc',
        'params' : {
            'pub_id'  : this.pub_data.pub_id,
            'servers' : this.pub_data.pub_servers.join(',')
        },
        'callback' : 'executeResponse'
    });
}

App.pubExecute = function () {
    this.socketSend({
        'action' : 'to_pub',
        'params' : {
            'pub_id'  : this.pub_data.pub_id,
            'servers' : this.pub_data.pub_servers.join(',')
        },
        'callback' : 'executeResponse'
    });
}

App.executeResponse = function(response) {
    this.debug(response)

    if (response.code != 'ok') {
        return;
    }

    switch (response.status) {
        case 'zip':
            $('#pub_result').append('<h5> · start zip (pub id=' + response.pub_id + ')</h5>');
            break;
        case 'zip_success':
            $('#pub_result').append('<h5> · zip finished</h5>');
            $('#btn-zip').text('Finished zip');
            $('#servers').show();
            this.pub_data.pub_id = response.pub_id;
            this.sycBind();
            break;
        case 'syc':
            $('#pub_result').append('<h5> · start sync</h5>');
            break;
        case 'syc_process':
            $('#pub_result').append('<h5> · server ' + response.server + ' sync finished</h5>');
            break;
        case 'syc_success':
            $('#btn-syc').text('Finished syc');
            $('#pub_result').append('<h5> · sync all finished</h5>');
            this.pubBind();
            break;
        case 'pub':
            $('#pub_result').append('<h5> · start pub</h5>');
            break;
        case 'pub_process':
            $('#pub_result').append('<h5> · server ' + response.server + ' pub finished</h5>');
            break;
        case 'pub_success':
            $('#pub_result').append('<h5> · pub all finished</h5>');
            $('#btn-pub').text('Finished pub');
            break;
    }
}