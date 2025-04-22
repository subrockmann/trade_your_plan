# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install Miniconda
RUN apt-get update && apt-get install -y wget && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/miniconda && \
    rm miniconda.sh && \
    /opt/miniconda/bin/conda init && \
    apt-get clean

# Add Miniconda to PATH
ENV PATH="/opt/miniconda/bin:$PATH"

# Copy the environment.yml file and create the environment
COPY environment.yml /app/environment.yml
RUN conda env create -f environment.yml && conda clean -afy



# Install git for cloning the repository
RUN apt-get update && apt-get install -y git

# Clone the pyfinsights repository
RUN git clone https://github.com/subrockmann/pyfinsights.git /tmp/pyfinsights

# Build the wheel for pyfinsights
RUN bash -c "source activate fin && pip install --no-cache-dir wheel && \
    cd /tmp/pyfinsights && \
    python setup.py bdist_wheel && \
    pip install --no-cache-dir dist/*.whl"

# Clean up the temporary directory
RUN rm -rf /tmp/pyfinsights

# Copy the application code to the container
COPY . /app

# Install pyfinsights from GitHub
# RUN pip install --no-cache-dir git+https://github.com/subrockmann/pyfinsights/artifacts/pyfinsights-0.1.4-py3-none-any.whl

# Expose the port that Streamlit uses
EXPOSE 8501

# Update CMD to directly use the Python executable from the `fin` environment
CMD ["/opt/miniconda/envs/fin/bin/python", "-m", "streamlit", "run", "trading_plan.py"]