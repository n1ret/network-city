document.body.onload= ()=>{
    function showError(err){
        $(".error").text(err);
        $(".error").removeClass("hide");
        $(".loader").addClass("hide");
        $(".modal").removeClass("hide");
    }
    $("#lgn").submit(e=>{
        e.preventDefault();
        var req={
            login:$("#lgn_val").val(),
            paswd:md5($("#pswd_val").val())
        }
        setTimeout(()=>{
            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                },
                body: JSON.stringify(req)
            }).then(response => {
                $("#lgn > input[type='submit']").prop("disabled",false);
                if(response.ok){
                    response.json().then(result=>{
                        if(result.ok){
                            window.location.reload();
                        } else {
                            showError(result.error);
                        }
                    });
                } else {
                    showError(response.statusText);
                }
            }).catch(err=>{
                showError(err);
            });
        },500);
        $("#lgn > input[type='submit']").prop("disabled",true);
        $(".loader").removeClass("hide");
        $(".modal").addClass("hide");
        $(".error").addClass("hide");
    });
}