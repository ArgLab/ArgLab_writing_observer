document.querySelector('#sign-in').addEventListener('click', function () {
    chrome.runtime.sendMessage({ message: 'login' }, function (response) {
        //once the user is signed in, closes the extension window
        if (response === 'success') window.close();
    });
});

document.querySelector('button').addEventListener('click', function () {
    chrome.runtime.sendMessage({ message: 'isUserSignedIn' }, function (response) {
        alert(response);
    });
});