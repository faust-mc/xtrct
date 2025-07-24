function success_msg(message = "Operation successful!") {
    toastr.clear();
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000,
        hideDuration: "0"
    };
    toastr.success(message);
}

function warning_msg(message = "Please check your input.") {
    toastr.clear();
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000,
        hideDuration: "0"
    };
    toastr.warning(message);
}

function error_msg(message = "Something went wrong!") {
    toastr.clear();
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000,
        hideDuration: "0"
    };
    toastr.error(message);
}

function info_msg(message = "Here’s some information.") {
    toastr.clear();
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000,
        hideDuration: "0"
    };
    toastr.info(message);
}

function showLoader() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoader() {
    document.getElementById('loadingOverlay').style.display = 'none';
}