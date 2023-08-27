$(function () {
    $('a#mi-formulario').on('click', function (e) {
        e.preventDefault();
        var longitud = $('#longitud_input').val();
        var latitud = $('#latitud_input').val();
        var fecha = $('#fecha_input').val();
        var dato = $('#dato_input').val();

        var umbral = $('#umbral-input').val();
        var sizeMax = $('#sizememory-input').val();



        $.ajax({
            url: '/validar-UI-data',
            type: 'POST',
            data: JSON.stringify({
                longitud: longitud,
                latitud: latitud,
                fecha: fecha,
                dato: dato,
                umbral: umbral,
                sizeMax : sizeMax
            }),
            contentType: 'application/json',
            dataType: 'json',
            success: function (data) {
                if (data.success) {
                    // Los datos del formulario son válidos, hacer algo con ellos
                    var newUrl = '/predecir-UI-data?dato=' + dato + '&fecha=' +
                        fecha + '&lon=' + longitud  + '&lat=' + latitud + '&umbral=' + umbral+ '&sizeMax=' + sizeMax;
                    window.location.href = newUrl;
                } else {
                    // Los datos del formulario no son válidos, mostrar mensajes de error
                    var errors = data.errors;
                    $('input.form-control').removeClass('is-invalid');
                    $('input.form-control').removeClass('is-valid');
                    $('input.form-control').next('.invalid-feedback').remove();
                    $.each(errors, function (key, value) {
                        var input = $('input[name=' + key + ']');
                        if (value.length === 0) {
                            input.addClass('is-valid');
                        } else {
                            input.addClass('is-invalid');
                            input.after('<div class="invalid-feedback">' + value + '</div>');
                        }

                    });
                }
            }
        });
    });
});