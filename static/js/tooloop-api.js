var TooloopAPI = function () {};


TooloopAPI.poweroff = function() {
    if( confirm("Are you sure, you want to power off the machine?") ) {

        $.ajax({ 
            url: "/tooloop/api/v1.0/system/poweroff",
            timeout: 1000
        }); 
        
        $('body').append(
            '<div id="off-black" class="off-cover"></div> \
            <div id="off-white" class="off-cover"></div> \
            <div id="off-logo" class="hex-logo"></div>'
            );
    }
};


TooloopAPI.rebooting = false;
TooloopAPI.rebootTime;
TooloopAPI.reboot = function() {
    if( confirm("Are you sure, you want to reboot the machine?") ) {
        TooloopAPI.rebooting = true;
        TooloopAPI.rebootTime = new Date();

        $.ajax({
            url: "/tooloop/api/v1.0/system/reboot",
            timeout: 1000
        }).done(function( data ) {
            // TODO: start some sort of PING to determin whether the system is back and hide the cover
        });
    }
}