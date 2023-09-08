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

    const tabs={
        marks:$("#markstab"),
        schedule:$("#scheduletab")
    }
    const tabs1={
        today:$("#todaytab"),
        tomorrow:$("#tomorrowtab")
    }
    $(".selecttab") > $(".selectvar").click((e)=>{
        const targt=$(e.target);
        if(targt.hasClass("selected")) return;
        targt.parent().trigger("selectionchange",targt.attr("name"));
        targt.siblings().each((i,el)=>{
            el.classList.remove("selected");
        })
        targt.addClass("selected");
    });
    $("#tabselect").on("selectionchange",(e,newtabname)=>{
        var prevtab,newtab;
        if(newtabname=="marks"){
            prevtab=tabs.schedule;
            newtab=tabs.marks;
        } else if (newtabname=="schedule"){
            yaCounter94877549.reachGoal('schedopen');
            prevtab=tabs.marks;
            newtab=tabs.schedule;
        }
        prevtab.css("display","none");
        newtab.css("display","block");
    });
    $("#tabselect1").on("selectionchange",(e,newtabname)=>{
        var prevtab,newtab;
        if(newtabname=="today"){
            prevtab=tabs1.tomorrow;
            newtab=tabs1.today;
        } else if (newtabname=="tomorrow"){
            prevtab=tabs1.today;
            newtab=tabs1.tomorrow;
        }
        prevtab.css("display","none");
        newtab.css("display","table");
    });

    history.pushState(null, null, window.location.pathname);
}