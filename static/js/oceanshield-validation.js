/**
 * OceanShield Form Validation
 * Validates citizen report form data
 */

const OceanShieldValidation = {
    /**
     * Validate report form data
     */
    validateReport(data) {
        const errors = [];

        // Description validation
        if (!data.description || data.description.trim().length === 0) {
            errors.push('Hazard description is required');
        } else if (data.description.trim().length < 10) {
            errors.push('Description must be at least 10 characters');
        } else if (data.description.trim().length > 2000) {
            errors.push('Description cannot exceed 2000 characters');
        }

        // Location validation
        if (!data.location || data.location.trim().length === 0) {
            errors.push('Location is required');
        } else if (data.location.trim().length < 3) {
            errors.push('Location must be at least 3 characters');
        }

        // Coordinates validation (optional but if provided, must be valid)
        if (data.latitude !== undefined && data.latitude !== null && data.latitude !== '') {
            const lat = parseFloat(data.latitude);
            if (isNaN(lat) || lat < -90 || lat > 90) {
                errors.push('Latitude must be a number between -90 and 90');
            }
        }

        if (data.longitude !== undefined && data.longitude !== null && data.longitude !== '') {
            const lon = parseFloat(data.longitude);
            if (isNaN(lon) || lon < -180 || lon > 180) {
                errors.push('Longitude must be a number between -180 and 180');
            }
        }

        // If one coordinate is provided, the other must also be provided
        const hasLat = data.latitude !== undefined && data.latitude !== null && data.latitude !== '';
        const hasLon = data.longitude !== undefined && data.longitude !== null && data.longitude !== '';

        if (hasLat && !hasLon) {
            errors.push('If latitude is provided, longitude must also be provided');
        }
        if (hasLon && !hasLat) {
            errors.push('If longitude is provided, latitude must also be provided');
        }

        // Date/time validation (optional)
        if (data.datetime && data.datetime !== '') {
            const dt = new Date(data.datetime);
            if (isNaN(dt.getTime())) {
                errors.push('Invalid date/time format');
            }
            // Don't allow future dates
            if (dt > new Date()) {
                errors.push('Date/time cannot be in the future');
            }
        }

        // Image validation (optional)
        if (data.image) {
            const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
            if (!allowedTypes.includes(data.image.type)) {
                errors.push('Image type must be JPEG, PNG, WebP, or GIF');
            }
            // Max 5MB
            if (data.image.size > 5 * 1024 * 1024) {
                errors.push('Image file size cannot exceed 5MB');
            }
        }

        // Reporter name validation (optional)
        if (data.reporter_name && data.reporter_name.trim().length > 100) {
            errors.push('Reporter name cannot exceed 100 characters');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    },

    /**
     * Clean and normalize report data
     */
    normalizeReport(data) {
        return {
            description: (data.description || '').trim(),
            location: (data.location || '').trim(),
            latitude: data.latitude !== '' ? parseFloat(data.latitude) : null,
            longitude: data.longitude !== '' ? parseFloat(data.longitude) : null,
            datetime: data.datetime || null,
            reporter_name: data.reporter_name ? (data.reporter_name || '').trim() : null,
            is_demo: data.is_demo === true
        };
    },

    /**
     * Format error messages for display
     */
    formatErrors(errors) {
        if (errors.length === 0) return '';
        if (errors.length === 1) return errors[0];
        return errors.map((e, i) => `${i + 1}. ${e}`).join('\n');
    }
};
