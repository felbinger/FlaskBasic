let infoIcon = '<span class="fa fa-info-circle"></span>';

function setCookie(name, value, expired) {
    // expired in minutes
    let d = new Date();
    d.setTime(d.getTime() + (expired*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function delCookie(name) {
    document.cookie = name+'=; Max-Age=-99999999;';
}

function validateEmail(email) {
    let re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function setStatusMessage(text, category='success') {
    // possible categories: success, warning, danger
    let field = document.getElementById('statusMsg');
    field.style.display = 'block';
    field.className = `alert alert-${category}`;
    field.innerHTML = `${infoIcon} ${text}`;
}

let config = () => {
    return config();
};

function login(username, password, token=null) {
    let data = { username: username, password: password };
    if (token !== null) {
        data.token = token;
    }
    axios.post('/api/auth', data)
        .then((response) => {
            // clear login fields
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';

            // set tokens as cookie
            setCookie('accessToken', response.data.accessToken, 15);
            setCookie('refreshToken', response.data.refreshToken, 360);

            // add tokens to flask session
            axios.post('/login', {
                accessToken: response.data.accessToken,
                refreshToken: response.data.refreshToken
            }).then((response) => {
                if (response.status === 200) {
                    window.location = '/';
                }
            }).catch((error) => {
                console.log(error);
            });
        })
        .catch((error) => {
            if (error.response.data.message !== null || error.response.data.message !== undefined) {
                switch (error.response.data.message) {
                    case 'Invalid credentials':
                        setStatusMessage('Invalid Credentials!', 'danger');
                        break;
                    case 'Missing 2fa token':
                        // show field to enter 2fa token
                        document.getElementById('2faField').style.display = 'block';
                        break;
                }
            }
        });
}

function logout() {
    axios.delete(`/api/auth/refresh/${getCookie('refreshToken')}`)
        .then((response) => {
            if (response.status === 200) {
                delCookie('accessToken');
                delCookie('refreshToken');
                // remove token from flask session cookie
                axios.post(`/logout`);
                window.location = '/login';
            } else {
                console.log(response.data)
            }
        })
        .catch((error) => {
            console.log(error.response.data)
        });
}

function uploadProfilePicture(file) {
    refreshToken(() => {
        let reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            axios.post('/api/upload', {
                file: reader.result
            }, config()).then((response) => {
                if (response.status === 201) {
                    setStatusMessage('Profile Picture has been updated!');
                    // todo clear cache (remove image) to load new image
                    //window.location.reload()
                } else {
                }
            }).catch((error) => {
                if (error && error.response && error.response.data && error.response.data.message) {
                    setStatusMessage(error.response.data.message, 'danger');
                } else {
                    console.log(error)
                }
            });
        };
        reader.onerror = error => {
            console.log(error);
            setStatusMessage('Unable to upload profile picture!', 'danger');
        };
    });
}

function modifyProfile(displayName, email, profilePicture, totp, gpg, totpToken=null) {
    refreshToken(() => {
        if (profilePicture !== undefined) {
            uploadProfilePicture(profilePicture);
        }
        // check if the entered email address is valid
        if (!validateEmail(email)) {
            setStatusMessage('Invalid E-Mail address!', 'danger');
        } else {
            axios.put('/api/users/me', {
                displayName: displayName,
                email: email,
                totp_enabled: totp,
                totp_token: totpToken
            }, config()).then((response) => {
                if (response.status === 200) {
                    setStatusMessage('Profile has been saved!');
                    // if 2fa has been disabled, hide input field for the token
                    if (!totp && document.getElementById("disable2fa")) {
                        document.getElementById("disable2fa").style.display = 'none';
                    }
                    if (response.data.data.hasOwnProperty('2fa_secret')) {
                        // @Security possible security vulnerability - todo find another way to setup 2fa
                        setCookie('2faSecret', response.data.data['2fa_secret'], 10);
                        window.location = '/profile/2fa';
                    }
                } else {
                    console.log(response);
                }
            }).catch((error) => {
                if (error && error.response && error.response.data && error.response.data.message) {
                    setStatusMessage(error.response.data.message, 'danger');
                } else {
                    console.log(error)
                }
            });
            if (gpg) {
                console.log("Setup gpg")
            }
        }
    });
}

function changePassword(password, password2) {
    refreshToken(() => {
        // check if the passwords are equal
        if (password !== password2) {
            setStatusMessage('The entered passwords are not the same!', 'danger');
        } else {
            // check if the password fits the requirements (min. 8 characters)
            if (password.length < 8) {
                setStatusMessage('Password is too short!', 'danger');
            } else {
                axios.put('/api/users/me', {
                    password: password
                }, config()).then((response) => {
                    if (response.status === 200) {
                        setStatusMessage('Password has been updated!');
                    } else {
                        console.log(response.data);
                    }
                }).catch((error) => {
                    if (error && error.response && error.response.data && error.response.data.message) {
                        setStatusMessage(error.response.data.message, 'danger');
                    } else {
                        console.log(error)
                    }
                });
            }
        }
    });
}

function enable2fa(token) {
    refreshToken(() => {
        if (isNaN(token) && token.length !== 6) {
            setStatusMessage("Token is invalid!", 'danger');
        } else {
            axios.post('/api/users/2fa', {
                token: token
            }, config()).then((response) => {
                if (response.status === 200) {
                    window.location = '/profile';
                    setStatusMessage('2FA has been enabled!');
                } else {
                    setStatusMessage('Token is invalid!', 'danger');
                }
            }).catch((error) => {
                if (error && error.response && error.response.data && error.response.data.message) {
                    setStatusMessage('Token is invalid!', 'danger');
                } else {
                    console.log(error)
                }
            });
        }
    });
}

function abort2faSetup() {
    refreshToken(() => {
        axios.delete('/api/users/2fa', {
            headers: {
                'Authorization': `Bearer ${getCookie('accessToken')}`
            }
        }).then(response => {
            if (response.status === 200 && response.data.data === '2fa secret has been disabled') {
                window.location = '/profile'
            }
        }).catch(error => {
            if (error && error.response && error.response.data && error.response.data.message) {
                setStatusMessage(error.response.data.message, 'danger');
            } else {
                console.log(error)
            }
        });
    });
}

function refreshToken(callback) {
    axios.post('/api/auth/refresh', {
        refreshToken: getCookie('refreshToken')
    }).then((response) => {
        if (response.status === 200) {
            setCookie('accessToken', response.data.accessToken, '15');
            return callback();
        } else {
            console.log(response.data)
        }
    }).catch((error) => {
        if (error && error.response && error.response.data && error.response.data.message) {
            if (error.response.data.message === 'Invalid refresh token') {
                // refresh token is invalid if not already jumped out
                delCookie('refreshToken');
                delCookie('accessToken');
                window.location = '/login'
            } else {
                console.log(error.response.data.message)
            }
        } else {
            console.log(error)
        }
    });
}

function enable_encrypted_mails(fingerprint) {
    axios.post('/api/users/gpg', {
        fingerprint: fingerprint
    }, config())
        .then((response) => {
            if (response.status === 201) {
                window.location = '/profile';
                setStatusMessage('Future mails will be encrypted!');
            } else {
                setStatusMessage('The submitted fingerprint is invalid!', 'danger');
            }
        }).catch((error) => {
            console.log(error.response.data)
        });
}
