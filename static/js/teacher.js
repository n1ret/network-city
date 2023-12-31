function openModal(){
    $(".headercont").removeClass("opened");
    $('.modalcont').removeClass('hide');
}
$(window).on('popstate',()=>{
    $('.modalcont').addClass('hide');
    history.pushState(null, null, window.location.pathname);
})
document.body.onload=()=>{
    $(".menu").css("left",Math.max($(".header").width()-$(".menu").width()+5,0)+"px");
    
    $(".menu").get(0).style.setProperty("--menu-height", $(".menu").height()+"px");
    $(".headercont").removeClass("opened");
    
    $(".openmenu").click(()=>{
        $(".headercont").toggleClass("opened");
    });

    $(window).click((e)=>{
        if($(".headercont").hasClass("opened")){
            if(!["menuitem","openmenu"].includes(e.target.className)){
                $(".headercont").removeClass("opened");
            }
        }
    });
    setTimeout(()=>{
        $(".loadercont").addClass("hide");
    },300);

    $(".modalcont").click((e)=>{
        if(e.target.className=="modalcont")
            $(".modalcont").addClass("hide");
    })

    function showError(err){
        $(".error").text(err);
        $(".error").removeClass("hide");
        $(".loadercont").addClass("hide");
    }
    
    const simpleBar = new SimpleBar($("#viewinfo").get(0));

    $("#class-select").change((e)=>{
        simpleBar.getContentElement().innerHTML = "";
        fetch('/api/get_class_students?'+ new URLSearchParams({
            classr: e.target.value
        })).then((resp)=>{
            $(".loadercont").addClass("hide");
            resp.json().then((res)=>{
                $("#student-select").html("");
                res.class_students.forEach(classm => {
                    $("#student-select").append(new Option(classm[0],classm[1]));
                });
            })
        });
        $(".loadercont").removeClass("hide");
    })
    $("#student-select").change((e)=>{
        simpleBar.getContentElement().innerHTML = "";
    });
    $("#class-select").change();

    $("#getinfo").submit(e=>{
        e.preventDefault();
        const req={
            class:$("#class-select").val(),
            student:$("#student-select").val()
        }
        fetch('/api/get_student_marks?'+ new URLSearchParams(req))
        .then((resp)=>{
            $(".loadercont").addClass("hide");
            resp.text().then((res)=>{
                simpleBar.getContentElement().innerHTML = res;
                simpleBar.recalculate();
            })
        });
        $(".loadercont").removeClass("hide");
    })
    
    $("#updinfo").submit(e=>{
        e.preventDefault();
        const req = new FormData();
        req.append("class",$("#class-select2").val());
        req.append("file",$('#inpfile').prop('files')[0]);
        fetch('/api/update_marks?'+ new URLSearchParams(req),{
            method:'POST',
            body: req
        })
        .then(resp=>{
            resp.json().then(res=>{
                if(res.ok){
                    window.location.reload();
                } else {
                    alert(res.error);
                }
            })
        });
        $(".loadercont").removeClass("hide");
    })
    
    $("#chng").submit(e=>{
        e.preventDefault();
        var req={
            user_id:my_user_id,
            old:md5($("#old_val").val()),
            new:md5($("#new_val").val())
        }
        setTimeout(()=>{
            fetch('/api/change_pass', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                },
                body: JSON.stringify(req)
            }).then(response => {
                $("#chng > input[type='submit']").prop("disabled",false);
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
            });
        },500);
        $("#chng > input[type='submit']").prop("disabled",true);
        $(".loadercont").removeClass("hide");
        $(".error").addClass("hide");
    });
    history.pushState(null, null, window.location.pathname);
}