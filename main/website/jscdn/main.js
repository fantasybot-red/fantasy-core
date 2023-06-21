let ison = false;

function opendev() {
    let root = document.getElementById('main');
    let db = document.getElementById("mobidropbar");
    let ic = document.getElementById("mobiicon");
    if (ison) {
        db.classList.remove(`opun`);
        root.classList.remove(`blurroot`)
        ic.innerText = 'menu';
        ison = false;
    } else {
        db.classList.add(`opun`);
        root.classList.add(`blurroot`)
        ic.innerText = 'close';
        ison = true;
    }
}

let icon = document.getElementById("mobiicon");
icon.addEventListener("click", opendev, true);

async function clearload() {
    let load = document.getElementById("loading")
    let root = document.getElementById("root")
    let loadcss = document.getElementById("loadingcss")
    root.classList.add("rootloading")
    load.style.opacity = "0";
    await new Promise(r => setTimeout(r, 1000));
    hasload = true
    loadcss.remove();
    load.remove();
    await new Promise(r => setTimeout(r, 100));
    root.style.opacity = "1";
    await new Promise(r => setTimeout(r, 1000));
    root.removeAttribute("style")
    root.removeAttribute("class")
}

window.addEventListener("load", clearload)